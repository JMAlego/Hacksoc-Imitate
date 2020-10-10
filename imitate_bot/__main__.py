"""The Hacksoc Slack Imitate Bot."""
import logging
from traceback import print_tb
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
        print_tb(error.__traceback__)
        print(error)
        print("Exception occurred, exiting...")
    bot.close()

    exit()


if __name__ == "__main__":
    main()
