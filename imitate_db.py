#!/usr/bin/env python

"""
  Database module for ImitateBot
  by Jacob Allen
"""

import os
import hashlib
import json
import time
import math

VERSION = "1.0.0"

EMPTY_META = {
  "version":"1.0.0",
  "names":{},
  "aliases":{}
}

EMPTY_USER = {
  "name": "",
  "last_update": None,
  "messages": []
}

class Enum(set):
  def __getattr__(self, name):
    if name in self:
      return name
    raise AttributeError

INTEGRITY = Enum(["OKAY",
                  "MISSING_USER_FILE",
                  "ALIAS_MISSMATCH",
                  "NAME_FILE_COLLISION",
                  "EXTRANEOUS_NAME_FILES"])

class ImitateDB(object):
  """ImitateBot database management and access class"""

  def __init__(self,
                data_directory="./data/imitate_db/",
                max_cache_entries=5,
                cache_flexability=2,
                flexible_cache_step=0.5
              ):
    self.data_directory = data_directory
    self.max_cache_entries = max_cache_entries if max_cache_entries > 0 else 1
    self.meta_file = os.path.join(data_directory, "meta.json")
    self.meta = EMPTY_META
    self.db_cache = {}
    self.access_lock = []
    self.flexable_cache_index = 0
    self.cache_flexability = cache_flexability if cache_flexability > -1 else 0
    self.flexible_cache_step = flexible_cache_step if flexible_cache_step > 0 else 0.5

    if not os.path.isdir(self.data_directory):
      os.makedirs(self.data_directory)

    if not os.path.isfile(self.meta_file):
      self._write_meta_file(EMPTY_META)

    self.meta = self._read_meta_file()

    if self.meta["version"] != VERSION:
      raise Exception("Existing DB is not compatible")

    integrity_result = self.integrity_check()
    if integrity_result != INTEGRITY.OKAY:
      raise Exception("Integrity violation, code: " + str(integrity_result))

  def __exit__(self, exc_type, exc_value, exc_traceback):
    self.close()

  def __del__(self):
    if self.meta and self.data_directory:
      self.close(write_back_cache=False)

  @staticmethod
  def _default_user_data(name):
    return {
      "name":name,
      "last_update": None,
      "messages": []
    }

  @staticmethod
  def _hash_name(name):
    hasher = hashlib.sha256()
    hasher.update(name)
    return hasher.hexdigest()

  def _get_true_name(self, name):
    if name in self.meta["aliases"].keys():
      return self.meta["aliases"][name]
    return name

  def _user_file_path(self, name, hashed=False):
    name = self._get_true_name(name)
    if hashed:
      user_hash = name
    else:
      user_hash = self._hash_name(name)
    return os.path.join(self.data_directory, "user_" + user_hash + ".json")

  def _write_user_file(self, name, data):
    user_file = self._user_file_path(name)
    while user_file in self.access_lock:
      time.sleep(0.01)
      print self.access_lock
    self.access_lock.append(user_file)
    with open(user_file, "w") as fp:
      json.dump(data, fp)
    self.access_lock.remove(user_file)

  def _read_user_file(self, name):
    user_file = self._user_file_path(name)
    while user_file in self.access_lock:
      time.sleep(0.01)
    self.access_lock.append(user_file)
    with open(user_file, "r") as fp:
      result = json.load(fp)
    self.access_lock.remove(user_file)
    return result

  def _write_meta_file(self, data):
    while self.meta_file in self.access_lock:
      time.sleep(0.01)
    self.access_lock.append(self.meta_file)
    with open(self.meta_file, "w") as fp:
      json.dump(data, fp)
    self.access_lock.remove(self.meta_file)

  def _read_meta_file(self):
    while self.meta_file in self.access_lock:
      time.sleep(0.01)
    self.access_lock.append(self.meta_file)
    with open(self.meta_file, "r") as fp:
      result = json.load(fp)
    self.access_lock.remove(self.meta_file)
    return result

  def close(self, write_back_cache=True):
    self.write_back(write_back_cache=write_back_cache)

  def write_back(self, write_back_cache=True):
    self._write_meta_file(self.meta)
    if write_back_cache:
      for name, data in self.db_cache.items():
        self._write_user_file(name, data)

  def integrity_check(self):
    name_files = []
    for entry in os.listdir(self.data_directory):
      if entry.endswith(".json") and entry.startswith("user_"):
        name_files.append(os.path.join(self.data_directory, entry))

    names_with_aliases = []
    for name in self.meta["aliases"].values():
      if name not in names_with_aliases:
        names_with_aliases.append(name)

    for name, name_hash in self.meta["names"].items():
      if name in names_with_aliases:
        names_with_aliases.remove(name)

      name_file_path = self._user_file_path(name_hash, hashed=True)

      if name_file_path not in name_files:
        if not os.path.isfile(name_file_path):
          return INTEGRITY.MISSING_USER_FILE
        return INTEGRITY.NAME_FILE_COLLISION
      else:
        name_files.remove(name_file_path)

    if names_with_aliases:
      return INTEGRITY.ALIAS_MISSMATCH

    if name_files:
      return INTEGRITY.EXTRANEOUS_NAME_FILES

    return INTEGRITY.OKAY

  def user_exists(self, name):
    return self.meta["names"].has_key(self._get_true_name(name))

  def add_user(self, name):
    if self.user_exists(name):
      return False
    self._write_user_file(name, self._default_user_data(name))
    self.meta["names"][name] = self._hash_name(name)
    return True

  def _in_cache(self, name):
    return self.db_cache.has_key(name)

  def _restrict_cache(self):
    max_entries = self.max_cache_entries + math.floor(self.flexable_cache_index)
    number_to_remove = len(self.db_cache) - max_entries
    if number_to_remove < 0:
      if self.flexable_cache_index > 0:
        self.flexable_cache_index -= self.flexible_cache_step
    elif number_to_remove > 0:
      if self.flexable_cache_index < self.cache_flexability:
        self.flexable_cache_index += self.flexible_cache_step
    if number_to_remove > 0:
      entries_to_remove = []
      for name, data in self.db_cache.items():
        if number_to_remove > len(entries_to_remove):
          entries_to_remove.append((name, data["last_update"]))
        else:
          for entry in entries_to_remove:
            if data["last_update"] > entry[1]:
              entries_to_remove.remove(entry)
              entries_to_remove.append((name, data["last_update"]))
      for to_remove in entries_to_remove:
        self._write_user_file(to_remove[0], self.db_cache[to_remove[0]])
        del self.db_cache[to_remove[0]]

  def _load_name_into_cache(self, name):
    if self.meta["names"].has_key(name):
      self._restrict_cache()
      if not self._in_cache(name):
        name_data = self._read_user_file(name)
        self.db_cache[name] = name_data
      self._restrict_cache()
      return True
    return False

  def get_name_messages(self, name):
    if self._load_name_into_cache(name):
      return self.db_cache[name]["messages"]
    return None

  def get_name_messages_string(self, name):
    result = self.get_name_messages(name)
    if result:
      return "\n".join(result)
    return None

  def add_message(self, name, message):
    if not self.user_exists(name):
      self.add_user(name)
    self._load_name_into_cache(name)
    self.db_cache[name]["messages"].append(message)
    self.db_cache[name]["last_update"] = time.time()

if __name__ == "__main__":
  print "Testing..."
  db = ImitateDB()
  db.close()
