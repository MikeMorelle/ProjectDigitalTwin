FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY . /app

ENV PYTHONPATH=/app


CMD ["python", "/app/sensor_stream_producer/producer.py"]