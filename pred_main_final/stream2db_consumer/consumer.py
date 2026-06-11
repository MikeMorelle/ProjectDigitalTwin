import pandas as pd, joblib, json, time
from kafka import KafkaConsumer
from db.db_client import get_connection, insert_result
from ml.models.infer_model import predict_anomaly
from config import INPUT_TOPIC

#CONSUMER
def create_consumer(topic, group_id="default-group", auto_offset="latest"):
    consumer = None
    while consumer is None:
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers="kafka:9092",
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset=auto_offset,
                group_id=group_id
            )
        except Exception as e:
            print("Kafka consumer error:", e)
            time.sleep(5)
    return consumer


consumer = create_consumer(INPUT_TOPIC, group_id="anomaly-consumer")
print("Consumer and Producer created, starting to consume messages...")

conn = get_connection()
print("Database connection established.")

bundle = joblib.load("ml/models/latest/ano_model.joblib")
feature_cols = bundle['feature_cols']

for msg in consumer:

    data = msg.value
    cycle = data["cycle"]

    for engine_data in data["engines"]:
        engine_id = engine_data["engine_id"]

        X = pd.DataFrame([engine_data])[feature_cols]
        
        score, pred = predict_anomaly(X)

        result = {
            "engine_id": engine_id,
            "cycle": cycle,
            "anomaly_score": float(score),
            "is_anomaly": int(pred <= 0)
        }
        
        insert_result(conn, result)