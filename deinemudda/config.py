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

from container_app_conf import ConfigBase
from container_app_conf.entry.int import IntConfigEntry
from container_app_conf.entry.range import RangeConfigEntry
from container_app_conf.entry.string import StringConfigEntry
from container_app_conf.source.env_source import EnvSource
from container_app_conf.source.yaml_source import YamlSource

from deinemudda.const import CONFIG_NODE_ROOT, CONFIG_NODE_TELEGRAM, DEFAULT_SQL_PERSISTENCE_URL, \
    CONFIG_NODE_PERSISTENCE, CONFIG_NODE_STATS, CONFIG_NODE_PORT, CONFIG_NODE_BEHAVIOUR, CONFIG_NODE_WORD_COUNT_RANGE, \
    CONFIG_NODE_CHAR_COUNT_RANGE


class AppConfig(ConfigBase):

    def __new__(cls, *args, **kwargs):
        yaml_source = YamlSource("deinemudda")
        yaml_source.load()
        data_sources = [
            EnvSource(),
            yaml_source
        ]
        return super(AppConfig, cls).__new__(cls, data_sources=data_sources)

    TELEGRAM_BOT_TOKEN = StringConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_TELEGRAM,
            "bot_token"
        ],
        example="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")

    SQL_PERSISTENCE_URL = StringConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_PERSISTENCE,
            "url"
        ],
        default=DEFAULT_SQL_PERSISTENCE_URL)

    WORD_COUNT_RANGE = RangeConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_BEHAVIOUR,
            CONFIG_NODE_WORD_COUNT_RANGE
        ],
        default="[1..10]"
    )

    CHAR_COUNT_RANGE = RangeConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_BEHAVIOUR,
            CONFIG_NODE_CHAR_COUNT_RANGE
        ],
        default="[3..255]"
    )

    STATS_PORT = IntConfigEntry(
        key_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_STATS,
            CONFIG_NODE_PORT
        ],
        default=8000
    )
