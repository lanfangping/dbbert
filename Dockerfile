# syntax=docker/dockerfile:1
FROM postgres:15
# WORKDIR /code
# ENV FLASK_APP=app.py
# ENV FLASK_RUN_HOST=0.0.0.0
# RUN apk add --no-cache gcc musl-dev linux-headers
# COPY requirements.txt requirements.txt
# RUN pip install -r requirements.txt
# EXPOSE 5000
# COPY . .
# CMD ["flask", "run"]

RUN apt-get update && apt-get install -y make
RUN apt-get update && apt-get install -y gcc
RUN apt-get update && apt-get install -y postgresql-server-dev-15