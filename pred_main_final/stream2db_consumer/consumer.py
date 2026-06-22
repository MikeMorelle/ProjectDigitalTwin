import json, time
from kafka import KafkaConsumer
from db.db_client import get_connection, insert_batch
from config import INPUT_TOPIC, KAFKA_BOOTSTRAP

#CONSUMER
def create_consumer(topic, group_id="default-group", auto_offset="latest"):
    consumer = None
    while consumer is None:
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset=auto_offset,
                group_id=group_id
            )
        except Exception as e:
            print("Kafka consumer error:", e)
            time.sleep(5)
    return consumer


consumer = create_consumer(INPUT_TOPIC, group_id="anomaly-consumer")

conn = get_connection()

for msg in consumer:

    data = msg.value
    
    insert_batch(conn, data["cycle"], data["engines"])