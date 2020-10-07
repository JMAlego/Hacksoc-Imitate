"""The Hacksoc Slack Imitate Bot."""
from configparser import ConfigParser

from .bot import ImitateBot


def main():
    """Enter main loop for normal bot operation."""
    config = ConfigParser()
    config.read("imitate.cfg")

    bot = ImitateBot(config.get("imitate_bot", "bot_auth_token"), "./data/imitate_db/")
    try:
        bot.handle_messages()
    except Exception as error:
        print(error.with_traceback())
        print("Exception occurred, exiting...")
    bot.close()


if __name__ == "__main__":
    main()
