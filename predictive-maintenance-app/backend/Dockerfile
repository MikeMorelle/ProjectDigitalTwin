#minimal python base image
FROM python:3.11-slim

#/app is the working directory in the container
WORKDIR /app

#copy dependencies
COPY requirements/backend.txt .

#install dependencies
RUN pip install --no-cache-dir -r backend.txt

#copy the rest of the code
COPY . .

#start FastAPI server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]