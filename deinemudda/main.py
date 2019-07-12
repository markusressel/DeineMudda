import logging
import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), "..", ".."))
sys.path.append(parent_dir)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

if __name__ == '__main__':
    from deinemudda.bot import DeineMuddaBot
    from deinemudda.config import AppConfig
    from deinemudda.persistence import Persistence

    config = AppConfig()
    persistence = Persistence(config)
    bot = DeineMuddaBot(config, persistence)
    bot.start()
