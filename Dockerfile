# Docker image for deineMuddaBot

FROM python:3.6
#-alpine

WORKDIR /app

RUN apt-get update
#RUN apk add bash musl-dev gcc libffi-dev libressl-dev mariadb-dev libxml2-dev libxslt-dev
RUN apt-get -y install gcc libffi-dev libssl-dev libxml2-dev libxslt-dev
#RUN python3 -m ensurepip && pip3 install --upgrade pip setuptools

RUN pip install --upgrade pip
RUN pip install --no-cache-dir psycopg2
RUN pip install pipenv

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN pipenv install --system --deploy

COPY . .

CMD [ "python", "./deinemudda/main.py" ]