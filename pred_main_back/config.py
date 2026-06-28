import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_DB=str(os.getenv("POSTGRES_DB", "predictive"))
POSTGRES_USER=str(os.getenv("POSTGRES_USER", "admin"))
POSTGRES_PASSWORD=str(os.getenv("POSTGRES_PASSWORD", "admin"))
POSTGRES_HOST=str(os.getenv("POSTGRES_HOST", "timescaledb"))
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))

KAFKA_BOOTSTRAP = "kafka:9092"

INPUT_TOPIC=str(os.getenv("INPUT_TOPIC", "sensor_stream"))
CONTROL_TOPIC = "control_topic"

PROD_SLEEP_SECONDS = int(os.getenv("PROD_SLEEP_SECONDS", 15))
ROLLING_WINDOW_SIZE = int(os.getenv("ROLLING_WINDOW_SIZE", 10))

SENSOR_COUNT = int(os.getenv("SENSOR_COUNT", 21))
SENSORS = [f"sensor_{i}" for i in range(1, SENSOR_COUNT + 1)]

OPS = ["op_1", "op_2", "op_3"]

SEQUENCE_LENGTH=30

fault_config = {
    "None": {},
    "Drift (+3) for sensor 9 in engine 3": {
        "3": {
            "sensor_9": {"type":"offset", "value":100}
        }
    },
    "Sensor Failure (NaN) for sensor 12 in engine 5": {
        "5": {
            "sensor_12": {"type": "nan"}
        }
    }
}