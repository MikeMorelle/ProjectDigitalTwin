import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_DB=str(os.getenv("POSTGRES_DB", "predictive"))
POSTGRES_USER=str(os.getenv("POSTGRES_USER", "admin"))
POSTGRES_PASSWORD=str(os.getenv("POSTGRES_PASSWORD", "admin"))
POSTGRES_HOST=str(os.getenv("POSTGRES_HOST", "timescaledb"))
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))

INPUT_TOPIC=str(os.getenv("INPUT_TOPIC", "sensor_data"))

PROD_SLEEP_SECONDS = int(os.getenv("PROD_SLEEP_SECONDS", 2))
ROLLING_WINDOW_SIZE = int(os.getenv("ROLLING_WINDOW_SIZE", 10))

SENSOR_COUNT = int(os.getenv("SENSOR_COUNT", 21))
SENSORS = [f"s{i}" for i in range(1, SENSOR_COUNT + 1)]