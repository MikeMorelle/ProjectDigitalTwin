FROM python:3.11-slim

WORKDIR /app

#copy dependencies
COPY requirements/streaming.txt .

#install dependencies
RUN pip install --no-cache-dir -r streaming.txt

COPY streaming/stream.py /app/stream.py

CMD ["python", "stream.py"]