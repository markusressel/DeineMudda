from container_app_conf import Config
from container_app_conf.entry.int import IntConfigEntry
from container_app_conf.entry.string import StringConfigEntry

from deinemudda.const import CONFIG_NODE_ROOT, CONFIG_NODE_TELEGRAM, DEFAULT_SQL_PERSISTENCE_URL, \
    CONFIG_NODE_PERSISTENCE, CONFIG_NODE_STATS, CONFIG_NODE_PORT


class AppConfig(Config):

    @property
    def config_file_names(self) -> [str]:
        return ["deinemudda"]

    TELEGRAM_BOT_TOKEN = StringConfigEntry(
        yaml_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_TELEGRAM,
            "bot_token"
        ])

    SQL_PERSISTENCE_URL = StringConfigEntry(
        yaml_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_PERSISTENCE,
            "url"
        ],
        default=DEFAULT_SQL_PERSISTENCE_URL)

    STATS_PORT = IntConfigEntry(
        yaml_path=[
            CONFIG_NODE_ROOT,
            CONFIG_NODE_STATS,
            CONFIG_NODE_PORT
        ],
        default=8000
    )
