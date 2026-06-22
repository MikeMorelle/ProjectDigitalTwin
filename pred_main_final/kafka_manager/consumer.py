import json, time
from kafka import KafkaConsumer
from db.db_client import get_connection, insert_batch
from config import INPUT_TOPIC, KAFKA_BOOTSTRAP

def deserializer(value):
    if value is None:
        return
    
    try:
        return json.loads(value.decode('utf-8'))
    except Exception as e:
        print("Unable to decode", e, flush=True)
        return None
    

class Consumer:
    def __init__(self):
        for i in range(10):
            try:
                self.consumer = KafkaConsumer(
                    INPUT_TOPIC,
                    bootstrap_servers=KAFKA_BOOTSTRAP,
                    value_deserializer=deserializer,
                    auto_offset_reset="latest",
                    group_id="anomaly-consumer"
                )
                break
            except Exception as e:
                print(f"Kafka consumer error at time step {i}:", e)
                time.sleep(5)
    
    def run(self):

        conn = get_connection()

        for msg in self.consumer:

            data = msg.value
            
            insert_batch(conn, data["cycle"], data["engines"])

if __name__ == "__main__":
    consumer = Consumer()
    consumer.run()