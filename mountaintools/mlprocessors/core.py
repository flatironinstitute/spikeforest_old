from . import validators
from .validators import FileExistsValidator, ValidationError

from functools import lru_cache
import argparse
import sys
import traceback
from .execute import execute
from .createjobs import createJob, createJobs


class ParserError(ValueError):
    pass


class InOutBase():
    def __init__(self, description=None, optional=False, multi=False, directory=False, validators=None, *args, **kwargs):
        self.description = description
        self.optional = optional
        self.directory = directory
        self.multi = multi
        self.validators = validators or []

    def prepare(self, arg):
        pass

    @property
    def spec(self):
        return {'name': self.name, 'description': self.description, 'optional': self.optional}

class Input(InOutBase):
    def __init__(self, description=None, optional=False, multi=False, directory=False, validators=None, *args, **kwargs):
        super().__init__(description, optional, multi,
                         directory, validators, *args, **kwargs)
        self.validators.append(FileExistsValidator())
        # self.formats = []

class Output(InOutBase):
    def __init__(self, description=None, optional=False, multi=False, validators=None, is_array=False, *args, **kwargs):
        directory = False
        super().__init__(description, optional, multi,
                         directory, validators, *args, **kwargs)
        self.is_array = is_array

class OutputArray(Output):
    def __init__(self, description=None, optional=False, multi=False, validators=None, *args, **kwargs):
        super().__init__(description, optional, multi,
                         validators, is_array=True, *args, **kwargs)

class StreamInput(Input):
    """
      Processor input that preps the file for reading
    """

    mode = 'rb'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'mode' in kwargs:
            self.mode = kwargs['mode']

    def prepare(self, arg):
        return open(arg, self.mode)


class StreamOutput(Output):
    """
        Processor output that preps the file for writing
    """
    mode = 'wb'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'mode' in kwargs:
            self.mode = kwargs['mode']

    def prepare(self, arg):
        return open(arg, self.mode)


class Parameter():
    def __init__(self, **kwargs):
        self.default = kwargs.get('default', None)
        self.description = kwargs.get('description', '')
        self.optional = kwargs.get('optional', False)
        self.multi = kwargs.get('multi', False)
        self.choices = kwargs['choices'] if 'choices' in kwargs else []
        self.validators = kwargs.get('validators', [])

    def __repr__(self):
        if hasattr(self, 'name'):
            return self.name
        return super().__repr__()

    def clean(self, value):
        try:
            return self.datatype(value)
        except:
            return value

    @property
    def spec(self):
        if isinstance(self.datatype, tuple):
            dt = "{major}<{minor}>".format(
                major=self.datatype[0].__name__, minor=self.datatype[1].__name__)
        else:
            dt = self.datatype.__name__
        if dt == 'str':
            dt = 'string'
        s = {'name': self.name, 'description': self.description,
             'datatype': dt, 'optional': self.optional}
        if self.optional or self.default:
            s['default_value'] = str(self.default)
        return s


class BoolParameter(Parameter):
    def __init__(self, description='', **kwargs):
        if 'description' not in kwargs:
            kwargs['description'] = description
        super().__init__(**kwargs)
        self.datatype = bool
        if 'choices' not in kwargs:
            self.choices = [True, False]

    def clean(self, value):
        if value == 'True' or value == 'true' or value == '1':
            return True
        return False


class StringParameter(Parameter):
    def __init__(self, description='', **kwargs):
        if 'description' not in kwargs:
            kwargs['description'] = description
        super().__init__(**kwargs)
        self.datatype = str
        if 'regex' in kwargs:
            self.validators.append(validators.RegexValidator(kwargs['regex']))


class ArithmeticParameter(Parameter):
    def __init__(self, description='', **kwargs):
        if 'description' not in kwargs:
            kwargs['description'] = description
        super().__init__(**kwargs)
        if 'min' in kwargs or 'max' in kwargs:
            self.validators.append(validators.ValueValidator(**kwargs))


class IntegerParameter(ArithmeticParameter):
    def __init__(self, description='', **kwargs):
        super().__init__(description, **kwargs)
        self.datatype = int


class FloatParameter(ArithmeticParameter):
    def __init__(self, description='', **kwargs):
        super().__init__(description, **kwargs)
        self.datatype = float


class IntegerListParameter(StringParameter):
    def __init__(self, description='', **kwargs):
        super().__init__(description, **kwargs)
        self.datatype = (list, int)

        def validate(value):
            vals = value.split(',')
            try:
                intvals = [int(x) for x in vals]
            except:
                raise ValidationError("Input data incorrect")
        self.validators.append(validate)

    def clean(self, value):
        vals = value.split(',')
        if not vals:
            return []
        return [int(x) for x in vals]


class FloatListParameter(StringParameter):
    def __init__(self, description='', **kwargs):
        super().__init__(description, **kwargs)
        self.datatype = (list, float)

        def validate(value):
            vals = value.split(',')
            try:
                floatvals = [float(x) for x in vals]
            except:
                raise ValidationError("Input data incorrect")
        self.validators.append(validate)

    def clean(self, value):
        vals = value.split(',')
        if not vals:
            return []
        return [float(x) for x in vals]


class ProcMeta(type):
    """
        The metaclass is responsible for processing a class definition.

        Current features:
            - cls.NAME is assembled from class name and contents of NAMESPACE (TODO: consider package/module name)
            - cls.VERSION is set to 0.0.1 if not defined explicitly
            - cls.DESCRIPTION is taken from docstring if not defined explicitly
            - cls.INPUTS is assembled from class definition
            - cls.OUTPUTS is assembled from class members definition
            - cls.PARAMETERS is assembled from class members definition


    """
    def __new__(cls, name, bases, attrs, **kwargs):
        super_new = super().__new__

        parents = [b for b in bases if isinstance(b, ProcMeta)]
        # don't process Processor
        if not parents:
            return super_new(cls, name, bases, attrs)

        # todo: remove detected ins,outs,params from attrs
        new_class = super_new(cls, name, bases, attrs, **kwargs)
        name_components = []
        if 'NAMESPACE' in attrs and attrs['NAMESPACE']:
            name_components.append(attrs['NAMESPACE'])
        if 'NAME' in attrs and attrs['NAME']:
            name_components.append(attrs['NAME'])
        else:
            name_components.append(name)
        new_class.NAME = '.'.join(name_components)
        if 'VERSION' not in attrs:
            new_class.VERSION = '0.0.1'
        if 'DESCRIPTION' not in attrs:
            if '__doc__' in attrs:
                doc = attrs['__doc__']
                # find first empty line
                empty_line = doc.find('\n\n')
                if empty_line >= 0:
                    doc = doc[:empty_line]
                doc = ' '.join([x.strip() for x in doc.strip().splitlines()])

                new_class.DESCRIPTION = doc
            else:
                new_class.DESCRIPTION = '{} MountainLab processor'.format(
                    new_class.NAME)

        new_class.__doc__ = new_class.DESCRIPTION
        # inherit from parent
        if not hasattr(new_class, 'INPUTS'):
            new_class.INPUTS = []
        else:
            new_class.INPUTS = new_class.INPUTS.copy()
        if not hasattr(new_class, 'OUTPUTS'):
            new_class.OUTPUTS = []
        else:
            new_class.OUTPUTS = new_class.OUTPUTS.copy()
        if not hasattr(new_class, 'PARAMETERS'):
            new_class.PARAMETERS = []
        else:
            new_class.PARAMETERS = new_class.PARAMETERS.copy()

        for attr in attrs:
            if isinstance(attrs[attr], Input):
                attrs[attr].name = attr
                new_class.INPUTS.append(attrs[attr])
            if isinstance(attrs[attr], Output):
                attrs[attr].name = attr
                new_class.OUTPUTS.append(attrs[attr])
            if isinstance(attrs[attr], Parameter):
                attrs[attr].name = attr
                if attrs[attr].default is not None and not attrs[attr].optional:
                    raise Exception(
                        "{}: Can't have a non-optional parameter with a default value".format(attr))
                new_class.PARAMETERS.append(attrs[attr])

        return new_class


class Processor(metaclass=ProcMeta):
    """
    Create a MountainLab processor.

    Main use of Processor is to serve as a base class for processors.
    A processor is described in a declarative manner, that is the usual
    approach is to derive a new class from it and declare entities such
    as processor inputs, outputs and parameters as class members.

    In most cases you will want to register the processor in a Registry and
    the registry will handle instantiating and running the processor as
    defined by command-line arguments. However it is also possible to
    instantiate the processor object manually and execute it like a function,
    configuring it with keyword arguments.

    """
    NAMESPACE = None
    VERSION = None
    """ Version of the processor """
    DESCRIPTION = None
    """ Textual description of the processor """
    COMMAND = None
    """
    Command to invoke the processor from the commandline.
    Usually this is determined automatically and should not be set manually.
    """
    USE_ARGUMENTS = True

    @classmethod
    def apply(cls, self, *args, **kwargs):
        """
        Applies kwargs arguments to the instance passed as the first
        argument to the call.

        For defined INPUTS, OUTPUTS and PARAMETERS the method extracts
        a corresponding value from kwargs and sets it as an instance attribute.
        For example, if the processor has a 'foo' parameter declared and
        'foo = something' is passed to apply(), self.foo will become
        'something'.
        """
        for key in kwargs:
            if key in [x.name for x in cls.INPUTS]:
                setattr(self, key, kwargs[key])
            if key in [x.name for x in cls.OUTPUTS]:
                setattr(self, key, kwargs[key])
            if key in [x.name for x in cls.PARAMETERS]:
                setattr(self, key, kwargs[key])

    def __init__(self, *args, **kwargs):
        """
        Initialize the instance using values from kwargs.
        """
        self.apply(self, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        # in order to validate arguments we need to pass them through
        # self.invoke() that requires them to be a list of strings

        arglist = []
        for key, value in kwargs.items():
            arglist.append('--'+key)
            if isinstance(value, list):
                serialized = ','.join([str(x) for x in value])
            else:
                serialized = str(value)
            arglist.append(serialized)
        try:
            self.invoke(args=arglist, _instance=self)
        except ParserError as exc:
            raise RuntimeError(
                'Provided arguments are not valid for this processor') from exc

    @classmethod
    @lru_cache()
    def spec(self):
        """
        Generate spec for the processor as a Python dictionary.

        A spec is a standard way to describe a MountainLab processor in a way
        that is easy to process, yet still understandable by humans.
        This method generates a Python dictionary that complies with a spec
        definition.
        """
        pspec = {}
        pspec['name'] = self.NAME
        pspec['version'] = self.VERSION
        pspec['description'] = self.DESCRIPTION
        # if hasattr(self, 'run') and callable(self.run):
        components = [sys.argv[0], self.NAME]
        if self.USE_ARGUMENTS:
            components.append('$(arguments)')
        pspec['exe_command'] = self.COMMAND or ' '.join(components)

        pspec['inputs'] = [inp.spec for inp in self.INPUTS]
        pspec['outputs'] = [out.spec for out in self.OUTPUTS]
        pspec['parameters'] = [param.spec for param in self.PARAMETERS]
        if hasattr(self, 'test') and callable(self.test):
            pspec['has_test'] = True

        return pspec

    @classmethod
    def invoke_parser(self, supparser=None, noexit=False):
        """
            Return a commandline parser (argparse) for the processor.
        """
        if supparser:
            parser = supparser.add_parser(
                self.NAME, description=self.DESCRIPTION)
        else:
            if noexit:
                class NoExitArgumentParser(argparse.ArgumentParser):
                    def exit(self, status=0, message=None):
                        raise ParserError()

                    def error(self, message):
                        raise ParserError()

                parser = NoExitArgumentParser(
                    prog=self.NAME, description=self.DESCRIPTION)
            else:
                parser = argparse.ArgumentParser(
                    prog=self.NAME, description=self.DESCRIPTION)

        def populate_parser(parser, dataset):
            for elem in dataset:
                opts = {}
                opts['help'] = elem.description
                opts['required'] = not elem.optional
                if elem.multi:
                    opts['action'] = 'append'
                parser.add_argument('--'+elem.name, **opts)

        # populate parser with INPUTS
        populate_parser(parser, self.INPUTS)
        # populate parser with OUTPUTS
        populate_parser(parser, self.OUTPUTS)
        # populate parser with PARAMETERS
        for param in self.PARAMETERS:
            opts = {}
            opts['help'] = param.description
            opts['required'] = not param.optional
            if isinstance(param.datatype, tuple):
                opts['type'] = str
                # opts['type'] = param.datatype[1]
            else:
                opts['type'] = param.datatype

            if param.multi:
                opts['action'] = 'append'
            if param.choices:
                if isinstance(param.choices, tuple):
                    # if choices is a tuple, assume it is a tuple of mappings
                    # and expand them
                    opts['choices'] = [choice[0] for choice in param.choices]
                else:
                    opts['choices'] = param.choices
            parser.add_argument('--'+param.name, **opts)

        if self.USE_ARGUMENTS:
            parser.add_argument('--_tempdir', required=False,
                                help=argparse.SUPPRESS)
        return parser

    @classmethod
    def invoke(proc, args=None, *, _instance=None, **kwargs):
        """
        Executes the processor passing given arguments.

        :param args: a list of parameters in --key=value format.
        """
        if args is None:
            args = []
        for kwargname in kwargs:
            args.append('--'+kwargname)
            args.append('{}'.format(kwargs[kwargname]))
        parser = proc.invoke_parser(noexit=(_instance is not None))
        opts = parser.parse_args(args)
        kwargs0 = {}

        def handle_set(opts, dataset, kwargs0, canMulti=False):
            for elem in dataset:
                elemname = elem.name
                # ml-run-process passes values for not provided inputs, outputs and params as empty strings ('')
                if hasattr(opts, elemname) and getattr(opts, elemname) not in [None, '']:
                    # value for element was given in the invocation
                    elemvalue = getattr(opts, elemname)
                    if canMulti and isinstance(elemvalue, list):
                        elemlist = elemvalue
                    else:
                        elemlist = [elemvalue]
                    for elemelem in elemlist:
                        for validator in elem.validators:
                            validator(elemelem)
                    if hasattr(opts, elem.name):
                        prepared = elem.prepare(elemvalue) or elemvalue
                        kwargs0[elem.name] = prepared
                elif elem.optional:
                    # value was not set but is optional so ignore it
                    kwargs0[elem.name] = None
                else:
                    # value was not set and is mandatory -- error
                    raise AttributeError(
                        'Missing value for {} '.format(elemname))

        try:
            handle_set(opts, proc.INPUTS, kwargs0, True)
            handle_set(opts, proc.OUTPUTS, kwargs0, True)

            for param in proc.PARAMETERS:
                if hasattr(opts, param.name) and getattr(opts, param.name) is not None and getattr(opts, param.name) is not '':
                    value = getattr(opts, param.name)
                    # validate if needed
                    for validator in param.validators:
                        validator(value)
                    # if param is a tuple of choices, each choice is a tuple itself
                    # with first element of the input value and second element
                    # containing the value to be passed to the processor
                    if param.choices and isinstance(param.choices, tuple):
                        for choice in param.choices:
                            if choice[0] == value:
                                kwargs0[param.name] = choice[1]
                                break
                    else:
                        kwargs0[param.name] = value
                elif param.optional:
                    kwargs0[param.name] = param.default
                else:
                    raise AttributeError(
                        'Missing value for {} parameter'.format(param.name))
            if not _instance:
                _instance = proc(**kwargs0)
            else:
                _instance.apply(_instance, **kwargs0)
            return _instance.run()
            # todo: cleanup
        except Exception as e:
            print("Error:", e)
#            traceback.print_exc()
            raise

    @classmethod
    def execute(proc, **kwargs):
        # if not _cache:
        #    proc.invoke(**kwargs)
        #    return
        return execute(proc, **kwargs)

    @classmethod
    def createJob(proc, **kwargs):
        return createJob(proc, **kwargs)

    @classmethod
    def createJobs(proc, argslist):
        return createJobs(proc, argslist)