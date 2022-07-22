FROM python:3.7.6-slim

WORKDIR /app
COPY . .
RUN \
  pip3 install -r requirements.txt

ENTRYPOINT ["gunicorn"]
CMD ["api:app", "-w","2", "--threads", "2", "-b", "0.0.0.0:8080"]

