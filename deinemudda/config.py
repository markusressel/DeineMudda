from container_app_conf import Config
from container_app_conf.entry.string import StringConfigEntry

from deinemudda.const import CONFIG_NODE_ROOT, CONFIG_NODE_TELEGRAM


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
