FROM python:3.7-alpine

RUN adduser -D fencing

WORKDIR /home/fencing

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn pymysql

COPY app app
COPY migrations migrations
COPY fencingtournamenttool.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP fencingtournamenttool.py

RUN chown -R fencing:fencing ./
USER fencing

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
