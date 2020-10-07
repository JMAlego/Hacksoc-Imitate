"""Imitate bot configuration."""
from configparser import ConfigParser


class ImitateConfig:
    """Imitate configuration wrapper."""

    def __init__(self, config_path: str = "imitate.cfg"):
        """Initialise configuration."""
        self._config = ConfigParser()
        self._config.read(config_path)

    def _get(self, key, default):
        return self._config.get("imitate_bot", key, fallback=default)

    @property
    def data_path(self) -> str:
        """Get "data_path" config value."""
        return self._get("data_path", "./data/")

    @property
    def bot_auth_token(self) -> str:
        """Get "bot_auth_token" config value."""
        return self._get("bot_auth_token", None)

    @property
    def bot_id(self) -> str:
        """Get "bot_id" config value."""
        return self._get("bot_id", None)

    @property
    def mention_users(self) -> bool:
        """Get "mention_users" config value."""
        return self._get("mention_users", False)

    @property
    def debug(self) -> bool:
        """Get "debug" config value."""
        return self._get("debug", False)
