#shared env variables, currently in .py for easy dev -> if in prod needs better security e.g. .env,...

POSTGRES_DB="predictive"
POSTGRES_USER="admin"
POSTGRES_PASSWORD="admin"
POSTGRES_HOST="timescaledb"
POSTGRES_PORT =5432

KAFKA_BOOTSTRAP ="kafka:9092"

INPUT_TOPIC="sensor_stream"
CONTROL_TOPIC = "control_topic"

SENSORS = [f"sensor_{i}" for i in range(1, 22)]

OPS = ["op_setting_1", "op_setting_2", "op_setting_3"]

#one exemplatory bias for sensor value -> gets logged in terminal for user
fault_config = {
    "None": {},
    "Sensor Failure (NaN) for sensor 12 in engine 5": {
        "5": {
            "sensor_12": {"type": "nan"}
        }
    }
}