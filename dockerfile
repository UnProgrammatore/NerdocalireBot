FROM python:3

RUN pip install python-telegram-bot
RUN pip install mariadb

ADD nerdocalire.py /

CMD [ "python", "./nerdocalire.py" ]