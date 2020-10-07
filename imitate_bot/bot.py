"""Core logic for Slack Imitate Bot."""
import signal

from .command import ParseError, is_possible_command, parse_command
from .interface import SlackInterface
from .database import ImitateDatabase
from .imitator import imitate

ABOUT_MESSAGE = "Hi! I'm an imitate bot running via the ReggieBot user.\nI'm a brand new 2020 implementation! I may be buggy still!"
SORRY_MESSAGE = "Sorry, I couldn't imitate that user as I don't have enough data on them yet."
IMITATE_TEMPLATE = """\
I think <@{user}> might say:
>>> {message}"""


class ImitateBot:
    """Imitate bot."""

    def __init__(self, token: str, data_path: str):
        """Initialise the bot."""
        self.interface = SlackInterface(token)
        self.db = ImitateDatabase(data_path)
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
                    user_to_imitate = parsed_command.data[0]
                    result = imitate(self.db.get_messages(user_to_imitate))
                    if result is None:
                        self.interface.send_message(SORRY_MESSAGE, message.channel)
                    else:
                        self.interface.send_message(
                            IMITATE_TEMPLATE.format(user=user_to_imitate, message=result),
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
