# Docker image for deineMuddaBot

FROM python:3.6
#-alpine

WORKDIR /app

RUN apt-get update
#RUN apk add bash musl-dev gcc libffi-dev libressl-dev mariadb-dev libxml2-dev libxslt-dev
RUN apt-get install gcc libffi-dev libssl-dev libxml2-dev libxslt-dev
#RUN python3 -m ensurepip && pip3 install --upgrade pip setuptools

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD [ "python", "./deinemudda/main.py" ]