"""The imitator for the imitate bot."""
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional

import markovify

MINIMUM_DATA = 1000


class ImitateResultStatus(Enum):
    """Represents the result state of imitating a user."""

    SUCCESS = auto()
    NOT_ENOUGH_DATA = auto()
    RETRIES_EXCEEDED = auto()
    PROMPT_TOO_SHORT = auto()
    INVALID_PROMPT = auto()
    UNKNOWN_ERROR = auto()


@dataclass
class ImitateResult:
    """Represents the result of attempting to imitate a user."""

    status: ImitateResultStatus
    result: Optional[str]

    def __str__(self) -> str:
        """Just return result as str."""
        return str(self.result)


def stringify_messages(messages: List[str]) -> str:
    """Get messages as a single string."""
    return "\n".join(messages)


def imitate(messages: List[str],
            state_size: int = 2,
            prompt: Optional[str] = None) -> ImitateResult:
    """Imitate a user based on messages."""
    stringified_messages = stringify_messages(messages)
    if len(stringified_messages) < MINIMUM_DATA:
        return ImitateResult(ImitateResultStatus.NOT_ENOUGH_DATA, None)

    model = markovify.NewlineText(stringified_messages, state_size=state_size)

    split_prompt = None
    prefix = ""
    if prompt is not None:
        split_prompt = tuple(model.word_split(prompt))
    if split_prompt is not None and len(split_prompt) < state_size:
        return ImitateResult(ImitateResultStatus.PROMPT_TOO_SHORT, None)
    if split_prompt is not None and len(split_prompt) != state_size:
        prefix = " ".join(split_prompt[:-state_size]) + " "
        split_prompt = split_prompt[-state_size:]

    try:
        result = model.make_sentence(tires=1000, max_words=2500, init_state=split_prompt)
    except KeyError:
        if prompt is not None:
            return ImitateResult(ImitateResultStatus.INVALID_PROMPT, None)

        return ImitateResult(ImitateResultStatus.UNKNOWN_ERROR, None)

    if result is None:
        return ImitateResult(ImitateResultStatus.RETRIES_EXCEEDED, None)

    return ImitateResult(ImitateResultStatus.SUCCESS, prefix + result)
