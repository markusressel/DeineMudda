#  Copyright (c) 2019 Markus Ressel
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
import os
import sys

from container_app_conf.formatter.toml import TomlFormatter

parent_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), "..", ".."))
sys.path.append(parent_dir)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

if __name__ == '__main__':
    from prometheus_client import start_http_server
    from deinemudda.bot import DeineMuddaBot
    from deinemudda.config import AppConfig
    from deinemudda.persistence import Persistence

    config = AppConfig()
    LOGGER.debug("Config:\n{}".format(config.print(TomlFormatter())))

    # start prometheus server
    start_http_server(config.STATS_PORT.value)

    persistence = Persistence(config)
    bot = DeineMuddaBot(config, persistence)

    bot.start()
