"""The imitator for the imitate bot."""
from typing import List, Optional

import markovify

MINIMUM_DATA = 1000


def stringify_messages(messages: List[str]) -> str:
    """Get messages as a single string."""
    return "\n".join(messages)


def imitate(messages: List[str], state_size=2) -> Optional[str]:
    """Imitate a user based on messages."""
    stringified_messages = stringify_messages(messages)
    if len(stringified_messages) < MINIMUM_DATA:
        return None
    model = markovify.NewlineText(stringified_messages, state_size=state_size)
    return model.make_sentence(tires=1000, max_words=2500)
