# Docker image for deineMuddaBot

FROM python:2.7
#-alpine

WORKDIR /app

RUN apt-get update
#RUN apk add bash musl-dev gcc libffi-dev libressl-dev mariadb-dev libxml2-dev libxslt-dev
RUN apt-get install gcc libffi-dev libssl-dev libxml2-dev libxslt-dev
#RUN python3 -m ensurepip && pip3 install --upgrade pip setuptools

RUN pip install python-telegram-bot==11.1.0
RUN pip install pattern

COPY bot.py ./

CMD python bot.py
