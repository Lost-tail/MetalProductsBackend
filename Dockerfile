# syntax=docker/dockerfile:1

FROM python:3.9.6
ENV PYTHONUNBUFFERED 1
RUN mkdir /app
WORKDIR /app
ADD requirements.txt /app
RUN pip install -r requirements.txt
COPY . .
WORKDIR /app/app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
