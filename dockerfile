FROM python:3

ADD nerdocalire.py /

RUN pip install python-telegram-bot
RUN pip install mariadb

CMD [ "python", "./nerdocalire.py" ]