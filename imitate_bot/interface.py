"""Slack Interface."""
from slacksocket import SlackSocket


class _PatchedSlackSocket(SlackSocket):
    """Patched version to patch minor issues."""

    def get_event(self, *etypes, timeout=None):
        """Patched get_event."""
        # The original can have negative timeouts which causes errors
        if timeout is not None and timeout < 0:
            timeout = 0
        return super().get_event(*etypes, timeout=timeout)


class SlackInterface:
    """A simplistic Slack RTM wrapper."""

    def __init__(self, token):
        """Initialise the interface."""
        self._socket = _PatchedSlackSocket(token)
        self._closed = False

    def stop(self):
        """Stop all infinite generator from messages call."""
        self._runningForever = False

    def close(self):
        """Close the interface.

        Must be called to allow thread to exit properly.
        """
        self._closed = True
        self.stop()
        self._socket.close()

    def messages(self):
        """Return a blocking generator yielding Slack messages."""
        if self._closed:
            raise Exception("Interface closed.")
        self._runningForever = True
        while self._runningForever:
            for event in self._socket.events("message", idle_timeout=1):
                if "user" not in event:
                    continue
                if "subtype" in event and event["subtype"] == "bot_message":
                    continue
                yield event
                if not self._runningForever:
                    break

    def send_message(self, text, channel):
        """Send a message to slack."""
        self._socket.send_msg(text, channel)
