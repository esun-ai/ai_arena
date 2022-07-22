FROM python:3.7.2-stretch

WORKDIR /app

RUN pip install --upgrade pip
COPY requirements.txt requirements.txt 
RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT ["python3"]
CMD ["app.py"]

