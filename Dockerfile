# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /pymodbus

COPY . .

RUN pip3 install -r requirements.txt && pip3 install -e .

