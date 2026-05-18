#minimal python base image
FROM python:3.11-slim

#/app is the working directory in the container
WORKDIR /app

#copy dependencies
COPY requirements/dashboard.txt .

#install dependencies
RUN pip install --no-cache-dir -r dashboard.txt

#copy the rest of the code
COPY . .

#start Streamlit app
CMD ["streamlit", "run", "dashboard/app.py", "--server.address=0.0.0.0", "--server.port=8501"]