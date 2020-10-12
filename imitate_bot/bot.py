"""Core logic for Slack Imitate Bot."""
import logging
import signal

from .command import ParseError, is_possible_command, parse_command
from .config import ImitateConfig
from .database import ImitateDatabase
from .imitator import ImitateResultStatus, imitate
from .interface import SlackInterface

ABOUT_MESSAGE = "Hi! I'm an imitate bot running via the ReggieBot user.\nI'm a brand new 2020 implementation! I may be buggy still!"
NOT_ENOUGH_DATA_MESSAGE = "Sorry, I couldn't imitate that user as I don't have enough data on them yet."
RETRIES_EXCEEDED_MESSAGE = "Sorry, I couldn't imitate that user because it took too many attempts. Trying again may work."
PROMPT_TOO_SHORT_MESSAGE = "Sorry, I couldn't imitate that user because the promp was too short. Prompts must be at least `depth` words (defaults to 2)."
INVALID_PROMPT_MESSAGE = "Sorry, I couldn't imitate that user because the promp has never been said by the user."
UNKNOWN_ERROR_MESSAGE = "Sorry, I couldn't imitate that user because of an unknown error."
IMITATE_TEMPLATE = """\
I think {user} might say:
>>> {message}"""
MENTION_TEMPLATE = "<@{user}>"
DEPTH_ERROR_MESSAGE = "Sorry, a depth (state size) of between 1-4 (inclusive) is required, other sizes will fail to produce output."

LOGGER = logging.getLogger("imitate_bot")


class ImitateBot:
    """Imitate bot."""

    def __init__(self, config: ImitateConfig):
        """Initialise the bot."""
        # There's probably a nicer way of handling logging config but this will do for now
        LOGGER.setLevel(logging.DEBUG if config.debug else logging.INFO)

        self.interface = SlackInterface(config.bot_auth_token)
        self.db = ImitateDatabase(config.data_path)
        self._config = config
        self._old_handler = signal.signal(signal.SIGINT, self._signal_handler)
        self._closed = False

    def _signal_handler(self, signal_number, _):
        """Handle a SIGINT signal."""
        if signal_number == signal.SIGINT:
            self.interface.stop()

    def _handle_imitate_command(self, command, message):
        """Handle the imitate user command."""
        user_to_imitate, *_ = command.data

        # Handle depth argument
        state_size = 2
        if "depth" in command.arguments:
            state_size = command.arguments["depth"]
        if state_size > 4 or state_size < 1:
            self.interface.send_message(DEPTH_ERROR_MESSAGE, message.channel)
            return

        prompt = None
        if "prompt" in command.arguments:
            prompt = command.arguments["prompt"]

        result = imitate(self.db.get_messages(user_to_imitate),
                         state_size=state_size,
                         prompt=prompt)

        if result.status == ImitateResultStatus.NOT_ENOUGH_DATA:
            self.interface.send_message(NOT_ENOUGH_DATA_MESSAGE, message.channel)

        elif result.status == ImitateResultStatus.RETRIES_EXCEEDED:
            self.interface.send_message(RETRIES_EXCEEDED_MESSAGE, message.channel)

        elif result.status == ImitateResultStatus.PROMPT_TOO_SHORT:
            self.interface.send_message(PROMPT_TOO_SHORT_MESSAGE, message.channel)

        elif result.status == ImitateResultStatus.INVALID_PROMPT:
            self.interface.send_message(INVALID_PROMPT_MESSAGE, message.channel)

        elif result.status == ImitateResultStatus.UNKNOWN_ERROR:
            self.interface.send_message(UNKNOWN_ERROR_MESSAGE, message.channel)

        else:
            if self._config.mention_users:
                user_mention = MENTION_TEMPLATE.format(user=user_to_imitate)
            else:
                user_mention = "they"
            self.interface.send_message(IMITATE_TEMPLATE.format(user=user_mention, message=result),
                                        message.channel)

    def handle_message(self, message):
        """Handle a single message."""
        if self._closed:
            raise Exception("Bot closed.")

        message_text: str = message["text"].strip()

        if is_possible_command(message_text):
            try:
                parsed_command = parse_command(message_text)
            except ParseError:
                self.interface.send_message(ABOUT_MESSAGE, message.channel)
            else:
                if parsed_command.action == "imitate_user":
                    self._handle_imitate_command(parsed_command, message)
        else:
            self.db.add_message(message.user.id, message["text"])

    def handle_messages(self):
        """Handle messages indefinitely."""
        if self._closed:
            raise Exception("Bot closed.")
        for message in self.interface.messages():
            self.handle_message(message)

    def close(self):
        """Close the bot.

        Must be called to allow main thread to exit properly.
        """
        self._closed = True
        signal.signal(signal.SIGINT, self._old_handler)
        self.interface.close()
        self.db.writeback()
