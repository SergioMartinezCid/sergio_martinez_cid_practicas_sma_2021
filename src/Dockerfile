FROM python:3.9

COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt
ENV TZ Europe/Madrid

WORKDIR /opt/app