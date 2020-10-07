"""The Hacksoc Slack Imitate Bot."""
import logging
from configparser import ConfigParser

from .bot import ImitateBot
from .config import ImitateConfig


def main():
    """Enter main loop for normal bot operation."""
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s')

    config = ImitateConfig()
    bot = ImitateBot(config)
    try:
        bot.handle_messages()
    except Exception as error:
        print(error.with_traceback())
        print("Exception occurred, exiting...")
    bot.close()

    exit()


if __name__ == "__main__":
    main()
