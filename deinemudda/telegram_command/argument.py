import logging

from deinemudda.telegram_command import escape_for_markdown

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class CommandArgument:

    def __init__(self, name: str, description: str, example: str, type: type = str, converter: callable = None,
                 default: any = None,
                 validator: callable = None):
        """
        Creates a command argument object
        :param name: the name of the command
        :param converter: an optional converter function to convert the string value to another type
        :param default: an optional default value
        :param validator: a validator function
        """
        self.name = name
        self.description = description
        self.example = example
        self.type = type
        if converter is None:
            if type is not str:
                raise ValueError("If you want to use a custom type you have to provide a converter function too!")
            self.converter = lambda x: x
        else:
            self.converter = converter
        self.default = default
        self.validator = validator

    def parse_arg(self, arg: str) -> any:
        """
        Tries to parse the given value
        :param arg: the string value
        :return: the parsed value
        """

        if self.default is not None and arg is None:
            return self.default

        parsed = self.converter(arg)
        if self.validator is not None:
            if not self.validator(parsed):
                raise ValueError("Invalid argument value: {}".format(arg))

    def generate_argument_message(self) -> str:
        """
        Generates the usage text for this argument
        :return: usage text line
        """
        message = "  {} ({}): {}".format(
            escape_for_markdown(self.name),
            escape_for_markdown(self.type.__name__),
            escape_for_markdown(self.description)
        )
        if self.default is not None:
            message += " (default: {}".format(escape_for_markdown(self.default))
        return message
