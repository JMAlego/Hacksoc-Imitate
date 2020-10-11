"""Core logic for Slack Imitate Bot."""
import logging
import signal

from .command import ParseError, is_possible_command, parse_command
from .config import ImitateConfig
from .database import ImitateDatabase
from .imitator import imitate
from .interface import SlackInterface

ABOUT_MESSAGE = "Hi! I'm an imitate bot running via the ReggieBot user.\nI'm a brand new 2020 implementation! I may be buggy still!"
SORRY_MESSAGE = "Sorry, I couldn't imitate that user as I don't have enough data on them yet."
IMITATE_TEMPLATE = """\
I think {user} might say:
>>> {message}"""
MENTION_TEMPLATE = "<@{user}>"

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

    def handle_message(self, message):
        """Handle a single message."""
        if self._closed:
            raise Exception("Bot closed.")
        if is_possible_command(message["text"]):
            try:
                parsed_command = parse_command(message["text"])
                if parsed_command.action == "imitate_user":
                    user_to_imitate, *_ = parsed_command.data

                    state_size = 2
                    if "depth" in parsed_command.arguments:
                        state_size = parsed_command.arguments["depth"]

                    result = imitate(self.db.get_messages(user_to_imitate), state_size=state_size)

                    if result is None:
                        self.interface.send_message(SORRY_MESSAGE, message.channel)
                    else:
                        if self._config.mention_users:
                            user_mention = MENTION_TEMPLATE.format(user_to_imitate)
                        else:
                            user_mention = "they"
                        self.interface.send_message(
                            IMITATE_TEMPLATE.format(user=user_mention, message=result),
                            message.channel)
            except ParseError:
                self.interface.send_message(ABOUT_MESSAGE, message.channel)
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
