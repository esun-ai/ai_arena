FROM python:3.7.2-stretch
USER root

WORKDIR /app
COPY requirements.txt /app
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . /app

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y libpq-dev gcc

ENTRYPOINT ["/bin/bash"]
