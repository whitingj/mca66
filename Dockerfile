FROM python:2-slim

WORKDIR /usr/src/app

RUN pip install flask pyserial flask-cors 

COPY . .

CMD [ "python", "./app.py" ]
