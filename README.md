# DeineMudda [![Build Status](https://travis-ci.org/markusressel/DeineMudda.svg?branch=master)](https://travis-ci.org/markusressel/DeineMudda)

Nee, deine Mudda!

# Configuration

DeineMudda uses [container-app-conf](https://github.com/markusressel/container-app-conf)
for configuration. Check out [deinemudda_example.yaml](https://github.com/markusressel/DeineMudda/blob/master/deinemudda_example.yaml)
to see what the **YAML** config would look like.

| Name                               | Description                              | Type     | Default                                |
|------------------------------------|------------------------------------------|----------|----------------------------------------|
| `DEINEMUDDA_TELEGRAM_BOT_TOKEN`    | The bot token used to authenticate the bot with telegram | `str` | `-` |
| `DEINEMUDDA_PERSISTENCE_URL`       | SQLAlchemy connection URL | `str` | `sqlite:///deinemudda.db` |
| `DEINEMUDDA_STATS_PORT`            | Prometheus statistics port | `int` | `8000` |


# Developer docs

## Setup

To install the `pattern` library used by this bot you probably have to install `python-mysqlclient` as a system package
manually.

## Debugging and execution

Because of [PEP 479](https://www.python.org/dev/peps/pep-0479/) which is not yet respected in the `pattern` library used
by this bot it is required to use a python 3 runtime lower than 3.7 so 3.6 is recommended.

### Postgres

```bash
docker run \
  --name postgres \
  -e POSTGRES_USER=deinemudda \
  -e POSTGRES_PASSWORD=deinemudda \
  -p 5432:5432 \
  -d postgres
```

### Base dir

Make sure to use the project base dir as the working directory and run:

```
python3 ./deinemudda/main.py
```

## Telegram bot config

For the bot to be able to read messages you have to set the `Privacy`
setting of your bot to `DISABLED` (using `/setprivacy` and `disable`).
Otherwise the bot is only allowed to read messages containing commands.

# Attributions

Thx to [@njamster](https://github.com/njamster) for coming up with the idea and first working version
of this bot.

# Contributing

GitHub is for social coding: if you want to write code, I encourage contributions through pull requests from forks
of this repository. Create GitHub tickets for bugs and new features and comment on the ones that you are interested in.

# License
```text
DeineMudda
Copyright (C) 2019  Markus Ressel

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```