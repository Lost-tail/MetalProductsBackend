# syntax=docker/dockerfile:1

FROM python:3.12.3-slim-bookworm
ENV PYTHONUNBUFFERED 1
RUN mkdir /app
WORKDIR /app
ADD requirements.txt /app
RUN pip install -r requirements.txt
COPY . .
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
