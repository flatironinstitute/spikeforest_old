import os

class ValidationError(ValueError):
    """
    Validation failed exception
    """
    pass

class Validator:
    """
    Base class for validators
    """
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, value):
        return self.validate(value)

    def validate(self, value):
        """
        Validation function. Accepts the value to be validated.
        """
        return True

class ValueValidator(Validator):
    """
    Validation of numeric values. Allows to specify range of accepted values
    by passing in 'min' and/or 'max' keyword arguments when constructing
    the validator.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'min' in kwargs: self.min = kwargs['min']
        if 'max' in kwargs: self.max = kwargs['max']

    def validate(self, value):
        if self.min and value < self.min: raise ValidationError("Value {} less than {}".format(value, self.min))
        if self.max and value > self.max: raise ValidationError("Value {} greater than {}".format(value, self.max))

class RegexValidator(Validator):
    """
    Validation against a given regular expression.
    """
    def __init__(self, regex, *args, **kwargs):
        """
        :param regex: Regular expression to match against.
        """
        super().__init__(*args, **kwargs)
        self.regex = regex

    def validate(self, value):
        import re
        if not re.fullmatch(self.regex, value): # since Python 3.4
            raise ValidationError("Value '{}' has to match regular expression {}".format(value, self.regex))

class FileExtensionValidator(Validator):
    def __init__(self, extensions, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if extensions is not None:
            extensions = [ ext.lower() for ext in extensions ]
        self.extensions = extensions

    def validate(self, value):
        name, extension = os.path.splitext(value)
        if self.extensions is not None and extension not in self.extensions:
            raise ValidationError('File extension {} is not allowed'.format(extension))

class FileExistsValidator(Validator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self, value):
        if not os.path.exists(value):
            raise ValidationError("Input file '{}' does not exist.".format(value))
