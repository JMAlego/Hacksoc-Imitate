#!/usr/bin/env python
from time import sleep
import signal
import sys
import re
import ConfigParser

import markovify
from slacksocket import SlackSocket
from imitate_db import ImitateDB

COMMAND_REGEX = re.compile(r"^!imitate <@(?P<user>U[A-Z0-9]+)>$", flags=re.IGNORECASE)

class ImitateBot(object):
  def __exit__(self, exc_type, exc_value, exc_traceback):
    self.close()

  def close(self):
    if self._initialised and self._started and not self._closing:
      self._closing = True
      self.slack.close()
      while self.slack._thread.isAlive():
        sleep(0.01)

  def __init__(self, bot_key, db, bot_id = None):
    if bot_key is None:
      raise Exception("Slack Bot Key Required")
    else:
      self.bot_key = bot_key
    self._initialised = True
    self._started = False
    self._closing = False
    self.slack = None
    self.db = db
    self.bot_id = bot_id

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
      mk_text = self.db.get_name_messages_string(name)
      mk = markovify.NewlineText(mk_text)
      return mk.make_sentence(max_words=2000, tries=50)
    return False

  def handle_message(self, event):
    if not event.event.has_key("user"):
      return
    if event.event.has_key("subtype") and event.event["subtype"] == "bot_message":
      return
    if self.bot_id != None and event.event["user"] == self.bot_id:
      return
    if event.event["text"].startswith("!imitate"):
      if event.event["text"] == "!imitate":
        self.slack.send_msg("Hi! I'm an experimental imitate bot running via the ReggieBot user.", channel_id=event.event["channel"], confirm=False)
      else:
        command = COMMAND_REGEX.match(event.event["text"])
        if command:
          msg = self.imitate(command.group("user"))
          if msg:
            self.slack.send_msg(msg, channel_id=event.event["channel"], confirm=False)
          else:
            if msg == None:
              self.slack.send_msg("Not enough data on user...", channel_id=event.event["channel"], confirm=False)
            else:
              self.slack.send_msg("User not found!", channel_id=event.event["channel"], confirm=False)
        else:
          self.slack.send_msg("Usage: !imitate @USERNAME", channel_id=event.event["channel"], confirm=False)
    else:
      self.db.add_message(event.event["user"], event.event["text"])


if __name__ == "__main__":
  config = ConfigParser.ConfigParser()
  config.read("imitate.cfg")

  print "Imitate Bot Initialising..."

  db = ImitateDB()
  bot = ImitateBot(config.get("imitate_bot", "bot_auth_token"), db, config.get("imitate_bot", "bot_id"))

  def _exit_signal_handler(sig, frame):
    print('Exiting...')
    bot.close()
    db.close()
    sys.exit(0)

  signal.signal(signal.SIGINT, _exit_signal_handler)
  signal.signal(signal.SIGTERM, _exit_signal_handler)

  print "Starting Bot..."
  bot.start()
