"""Database for imitate bot."""
from hashlib import sha256
from json import dump as json_dump
from json import load as json_load
from os import listdir, path
from time import time
from typing import Dict, List, Optional


class UserData:
    """User data."""

    def __init__(self, data_path: str, user_id: str, new_user=False):
        """Initialise user data."""
        if user_id.startswith("U") and len(user_id) < 64:
            user_id = UserData.convert_id(user_id)
        if len(user_id) > 64:
            raise Exception("Invalid user ID '{}'".format(user_id))

        self.user_id = user_id
        self.last_update = time()
        self.last_access = time()
        self._messages: List[str] = []
        self.data_path = data_path
        self._loaded = new_user

    @staticmethod
    def from_file(file_path: str) -> "UserData":
        """Create a UserData instance from a file."""
        file_name = path.basename(file_path)

        if not file_name.startswith("user_"):
            raise Exception("Invalid file name")

        return UserData(path.dirname(file_path), file_name[len("_user"):-len(".json")])

    @property
    def messages(self) -> List[str]:
        """Get messages."""
        self.load()
        self.last_access = time()
        return self._messages

    def add_message(self, message):
        """Add a message."""
        self.load()
        self._messages.append(message)
        self.last_update = time()

    def load(self):
        """Load user data from file."""
        if not self._loaded:
            with open(self.file_path, "r") as file_handle:
                data = json_load(file_handle)
                self._messages = data["messages"]
                self.last_update = data["last_update"]
                self._loaded = True

    def unload(self):
        """Unload data (and save)."""
        if self._loaded:
            self.save()
            self._messages = None
            self.last_update = None
            self._loaded = False

    @staticmethod
    def convert_id(slack_user_id: str) -> str:
        """Convert slack ID to database ID."""
        hasher = sha256()
        hasher.update(slack_user_id.encode("utf-8"))
        return hasher.hexdigest()

    @property
    def file_name(self) -> str:
        """Get file name."""
        return "user_{}.json".format(self.user_id)

    def to_dict(self):
        """Get dictionary representation."""
        return {"messages": self.messages, "last_update": self.last_update}

    @property
    def file_path(self) -> str:
        """Get data file path."""
        return path.join(self.data_path, self.file_name)

    def save(self):
        """Save data without unloading."""
        if self._loaded:
            print("Saving {}".format(self.file_path))
            with open(self.file_path, "w") as file_handle:
                json_dump(self.to_dict(), file_handle)


class ImitateDatabase:
    """Imitate database."""

    def __init__(self, data_path: str, writeback_interval: int = 2 * 60, unload_time: int = 5 * 60):
        """Initialise database."""
        self._writeback_interval = writeback_interval
        self._unload_time = unload_time
        self._last_writeback = time()
        data_files = filter(lambda x: x.startswith("user_"), listdir(data_path))
        users: List[UserData] = list(
            map(UserData.from_file, map(lambda x: path.join(data_path, x), data_files)))
        self._users: Dict[str, UserData] = {user.user_id: user for user in users}
        self._data_path = data_path

    def _check_for_writeback(self):
        old_time = self._last_writeback
        self._last_writeback = time()
        if self._last_writeback - old_time > self._writeback_interval:
            self.writeback()

    def writeback(self):
        """Writeback all data to the database."""
        for user in self._users.values():
            user.save()
        self._last_writeback = time()

    def _check_for_unload(self):
        for user in self._users.values():
            if time() - user.last_access > self._unload_time:
                user.unload()

    def get_messages(self, user_id: str) -> List[str]:
        """Get messages for a user."""
        user_id = UserData.convert_id(user_id)
        if user_id not in self._users:
            self._users[user_id] = UserData(self._data_path, user_id, new_user=True)

        messages = self._users[user_id].messages

        self._check_for_writeback()
        self._check_for_unload()

        return messages

    def add_message(self, user_id: str, message: str):
        """Add a message to a user."""
        user_id = UserData.convert_id(user_id)
        if user_id not in self._users:
            self._users[user_id] = UserData(self._data_path, user_id, new_user=True)
        self._users[user_id].add_message(message)
        self._check_for_writeback()
        self._check_for_unload()
