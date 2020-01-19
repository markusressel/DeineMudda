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

DEINE_MUDDA_VERSION = "1.3.7"

CONFIG_NODE_ROOT = "deinemudda"
CONFIG_NODE_TELEGRAM = "telegram"

CONFIG_NODE_BEHAVIOUR = "behaviour"
CONFIG_NODE_WORD_COUNT_RANGE = "word_count_range"
CONFIG_NODE_CHAR_COUNT_RANGE = "char_count_range"

CONFIG_NODE_PERSISTENCE = "persistence"

CONFIG_NODE_STATS = "stats"
CONFIG_NODE_PORT = "port"

CONFIG_NODE_VOTING = "voting"

DEFAULT_SQL_PERSISTENCE_URL = "sqlite:///deinemudda.db"

COMMAND_COMMANDS = ['help', 'h']
COMMAND_VERSION = ['version', 'v']
COMMAND_CONFIG = ['config', 'c']
COMMAND_STATS = 'stats'
COMMAND_MUDDA = 'mudda'

COMMAND_LIST_USERS = ['users', 'u']
COMMAND_BAN = ['ban', 'b']
COMMAND_UNBAN = ['unban', 'ub']

COMMAND_GET_SETTINGS = ['settings', 's']
COMMAND_SET_ANTISPAM = 'set_antispam'
COMMAND_SET_CHANCE = 'set_chance'

SETTINGS_ANTISPAM_ENABLED_KEY = "antispam"
SETTINGS_ANTISPAM_ENABLED_DEFAULT = "on"
SETTINGS_TRIGGER_PROBABILITY_KEY = "TriggerChance"
SETTINGS_TRIGGER_PROBABILITY_DEFAULT = "0.01"

# Voting button IDs
VOTE_BUTTON_ID_THUMBS_UP = "0-thumbsup"
VOTE_BUTTON_ID_THUMBS_DOWN = "1-thumbsdown"
