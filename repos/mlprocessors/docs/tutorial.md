# Tutorial

## Installation

    pip3 install mlprocessors

## Basics of a processor

MountainLab processor is an algorithm manipulating a set of ``Input`` files to produce ``Output`` files
accoding to ``Parameter`` values.

To create a processor you define a Python class by deriving it from ``Processor`` class::

    from mlprocessors.core import Processor

    class EmptyProcessor(Processor):
        pass

While this processor does nothing it is a perfectly valid implementation.
To make it available to MountainLab it needs to be associated with a processor registry::

    from mlprocessors.registry import registry

    registry.register(EmptyProcessor)

The registry needs to be activated by calling its ``process()`` method::

    import sys

    registry.process(sys.argv[1:]) # pass in command line arguments

The complete code looks as follows::

    #!/usr/bin/env python3

    from mountainlab_pytools.mlprocessors.core import Processor
    from mountainlab_pytools.mlprocessors.registry import registry
    import sys

    class EmptyProcessor(Processor):
        pass

    registry.register(EmptyProcessor)

    registry.process(sys.argv[1:])

The code should be put in a file with ``.mp`` extension and made executable::

    chmod +x processors.mp

## Executing code

To be useful a processor needs to execute code. It should be put into a method called ``run()``::

    class HelloWorldProcessor(Processor):
        def run(self):
            print("Hello World!")

A processor can execute arbitrary Python code however its basic purpose is to produce output.

## Producing output

Output files produced by a processor should be declared in the processor class::

    from mlprocessors.core import Output

    class HelloWorldProcessor(Processor):
        outfile = Output()

When the processor is executed, the field is filled with a file path where the output should be generated.
This path can be used in the run method::

        def run(self):
            fh = open(self.outfile, 'w')
            fh.write('Hello World!')
            fh.close()

## Reading input

Similar to having one or more ``Output``, a processor can work on data read from ``Input`` files::

    class CopyProcessor(Processor):
        input = Input()
        output = Output()

        def run(self):
            fromFile = open(self.input)
            toFile = open(self.output, 'w')
            toFile.write(fromFile.read())

When using Input, MLProcessors performs some basic checks when a processor is ran such
as checking whether the file specified by the user exists::

    ./example.mp CopyProcessor --input /tmp/aa --output /tmp/bb
    Error: Input file '/tmp/aa' does not exist.

Additional checks can be introduced in two ways.

One way is to use a subclass of ``Input`` class that contains those checks,
e.g. using ``MdaInput`` would check the file extension of the given path against a ``*.mda`` pattern.

Another way you can use when a suitable subclass does not exist is to pass in additional validators
when declaring the input::

    class Proc(Processor):
        fin = Input(
            validators = [ RegexValidator(r'dataset_[0-9]+\.dat') ]
        )

## Making the processor configurable

It's a typical situation for the processor to alter its behavior
based on one or more values the user can set before the processor
is executed.
These can be exposed in a ``Processor`` by declaring instances
of ``Parameter``.
This class is rarely used directly and it's more straightforward
to use one of its subclasses such as ``IntegerParameter`` or ``StringParameter``.

    from mlprocessors.core import IntegerParameter

    class CopyProcessor(Processor):
        input = Input()
        output = Output()

        size = IntegerParameter('Amount of data to copy')

        def run(self):
            fromFile = open(self.input)
            toFile = open(self.output, 'w')
            toFile.write(fromFile.read(self.size))

The code above declares a mandatory integer parameter called ``size``
that accepts any integer.
This forces the user to provide the value for this parameter which is inconvenient.
The most common case when copying files is to copy the entire file (which will happen if ``-1`` is passed to ``read()``)
so ``-1`` can be made a default value for the parameter:

    size = IntegerParameter('Amount of data to copy', optional=True, default=-1)


Note that, similar to ``Parameter`` also ``Input`` and ``Output`` can be made optional using the same approach.

### Range of allowed values

With ``IntegerParameter`` and ``FloatParameter`` one can provide a range of values accepted
by such parameters by setting ``min`` and/or ``max``.

    threshold = FloatParameter('Threshold value', min=0.0, max=1.0, optional=True, default=0.5)

Any try of providing values outside the declared range will result in a validation error and
the processor will not execute.
This simplifies the actual ``run()`` method of the processor as all validation will already have been
done when the processor runs.

