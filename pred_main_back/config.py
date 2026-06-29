POSTGRES_DB="predictive"
POSTGRES_USER="admin"
POSTGRES_PASSWORD="admin"
POSTGRES_HOST="timescaledb"
POSTGRES_PORT =5432

KAFKA_BOOTSTRAP ="kafka:9092"

INPUT_TOPIC="sensor_stream"
CONTROL_TOPIC = "control_topic"

ROLLING_WINDOW_SIZE =10

SENSORS = [f"sensor_{i}" for i in range(1, 22)]

OPS = ["op_1", "op_2", "op_3"]

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