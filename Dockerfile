# syntax=docker/dockerfile:1

FROM python:3.9-slim-buster

WORKDIR /pymodbus

EXPOSE 8080
EXPOSE 5020

COPY . .

RUN pip install -r requirements.txt && pip install -e .

CMD [ "pymodbus.server", "--host", "127.0.0.1", "--web-port", "8080", "--no-repl", "run", "--modbus-port", "5020", "--modbus-server", "tcp" ]
