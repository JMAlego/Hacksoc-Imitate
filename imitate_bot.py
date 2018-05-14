#!/usr/bin/env python
# -*- coding: utf-8 -*-
from time import sleep
import signal
import sys
import re
import ConfigParser

import markovify
from slacksocket import SlackSocket
from imitate_db import ImitateDB

COMMAND_REGEX = re.compile(r"^!imitate <@(?P<user>U[A-Z0-9]+)>[ ]*$", flags=re.IGNORECASE)


class ImitateBot(object):
  def __exit__(self, exc_type, exc_value, exc_traceback):
    self.close()

  def close(self):
    if self._initialised and self._started and not self._closing:
      self._closing = True
      self.slack.close()
      while self.slack._thread.isAlive():
        sleep(0.01)

  def __init__(self, bot_key, db_in, bot_id=None, debug_mode=False, imitate_attempts=100):
    if bot_key is None:
      raise Exception("Slack Bot Key Required")
    else:
      self.bot_key = bot_key
    self._initialised = True
    self._started = False
    self._closing = False
    self.slack = None
    self.db = db_in
    self.bot_id = bot_id
    self.debug_mode = debug_mode
    self.imitate_attempts = imitate_attempts

  def start(self):
    self.slack = SlackSocket(
      self.bot_key,
      translate=False,
      event_filters=["message"]
    )
    self._started = True
    for event in self.slack.events():
      self.handle_message(event)

  def imitate(self, name):
    if self.slack._find_user_name(name):
      if self.debug_mode:
        print "[debug] Generating chain for:", name if name else None
      mk_text = self.db.get_name_messages_string(name)
      if self.debug_mode:
        print "[debug] Got", len(mk_text if mk_text else ""), "characters of data"
      if mk_text is None:
        return None
      mk = markovify.NewlineText(mk_text)
      result = None
      for _ in range(self.imitate_attempts):
        result = mk.make_sentence(tires=100, max_words=2500)
        if result:
          break
      return result
    if self.debug_mode:
      print "[debug] Could not find user:", name if name else None
    return False

  def handle_message(self, event):
    if "user" not in event.event:
      return
    if event.event.get("subtype") == "bot_message":
      return
    if self.bot_id is not None and event.event["user"] == self.bot_id:
      return
    if event.event["text"].startswith("!imitate"):
      if event.event["text"] == "!imitate":
        self.slack.send_msg("Hi! I'm an experimental imitate bot running via the ReggieBot user.", channel_id=event.event["channel"], confirm=False)
      else:
        command = COMMAND_REGEX.match(event.event["text"])
        if command:
          msg = self.imitate(command.group("user"))
          if msg:
            self.slack.send_msg("I think <@" + command.group("user") + "> might say:\n" + ">>> " + msg, channel_id=event.event["channel"], confirm=False)
          else:
            if msg is None:
              self.slack.send_msg("Not enough data on user...", channel_id=event.event["channel"], confirm=False)
            else:
              self.slack.send_msg("User not found!", channel_id=event.event["channel"], confirm=False)
        else:
          self.slack.send_msg("Usage: !imitate @USERNAME", channel_id=event.event["channel"], confirm=False)
          print "[debug] Weird stuff:", event.event
    else:
      self.db.add_message(event.event["user"], event.event["text"])


if __name__ == "__main__":
  config = ConfigParser.ConfigParser()
  config.read("imitate.cfg")

  print "Imitate Bot Initialising..."

  debug = config.get("imitate_bot", "debug").lower() == "true" or config.get("imitate_bot", "debug") == "1"

  db = ImitateDB(debug_mode=debug)
  bot = ImitateBot(config.get("imitate_bot", "bot_auth_token"), db, config.get("imitate_bot", "bot_id"), debug_mode=debug)

  def _exit_signal_handler(sig, frame):
    print('Exiting...')
    bot.close()
    db.close()
    sys.exit(0)

  signal.signal(signal.SIGINT, _exit_signal_handler)
  signal.signal(signal.SIGTERM, _exit_signal_handler)

  print "Starting Bot..."
  bot.start()
