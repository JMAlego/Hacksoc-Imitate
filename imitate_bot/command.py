"""Command parser for imitate bot."""
from lark import Lark, Transformer, LexError, ParseError as LarkParseError
from dataclasses import dataclass
from typing import List, Tuple, Union, Dict

command_grammar = r"""
start: "!imitate" _WS+ command (_WS+ arguments)?
?command: command_imitate_user

command_imitate_user: USERNAME

arguments: [argument (_WS+ argument)*]
?argument: argument_depth
        | argument_prompt
argument_depth: "depth" "=" INT
argument_prompt: "prompt" "=" ESCAPED_STRING

USERNAME: "<@" ("U" | "u") (LETTER | DIGIT)+ ">"
_WS: WS

%import common.ESCAPED_STRING
%import common.INT
%import common.LETTER
%import common.DIGIT
%import common.WS
"""


class ParseError(Exception):
    """Represents a command parse error."""


ArgumentData = Union[int, str]


@dataclass
class Command:
    """Bot command class."""

    action: str
    data: List[str]
    arguments: Dict[str, ArgumentData]

    def __init__(self, children):
        """Initialise command class."""
        action, *rest = children

        self.action, *self.data = action

        self.arguments = []
        for item in rest:
            item_type, item_value = item
            if item_type == "arguments":
                argument_key, argument_value = item_value
                self.arguments[argument_key] = argument_value


class CommandTransformer(Transformer):
    """Transform parse tree."""

    start = Command
    command_imitate_user = lambda _, x: ("imitate_user", x[0].value[2:-1])
    arguments = lambda _, x: ("arguments", x)
    argument_depth = lambda _, x: ("depth", int(x[0].value))
    argument_prompt = lambda _, x: ("prompt", str(x[0].value[1:-1]))


parser = Lark(command_grammar, parser='lalr', transformer=CommandTransformer())


def is_possible_command(message: str) -> bool:
    """Check if the message may be a command."""
    return message.startswith("!imitate")


def parse_command(message: str) -> Command:
    """Parse command message."""
    try:
        parsed = parser.parse(message)
    except LexError:
        raise ParseError("Error lexing command.")
    except LarkParseError:
        raise ParseError("Error parsing command.")

    return parsed


__all__ = ["parse_command", "is_possible_command", "ParseError", "Command"]
