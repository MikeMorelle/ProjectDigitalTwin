import json, time
from kafka import KafkaProducer, KafkaConsumer
from ml.data.load_data import load_data
from kafka_manager.state_manager import ProducerConfig
from config import SENSORS, INPUT_TOPIC, KAFKA_BOOTSTRAP

def serializer(message):
    return json.dumps(message).encode() 

class Producer:
    def __init__(self):
        for i in range(10):
            try:
                self.producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP, value_serializer=serializer)
                break
            except Exception as e: 
                print(f"Error initializing Kafka Producer in {i}th attempt.")

    def stream(self, config: ProducerConfig, stop_event):
        try:    
            df = load_data(config.dataset)
            
            for cycle, cycle_rows in df.groupby("cycle", sort=True):

                if stop_event.is_set():
                    break   

                cycle_rows = cycle_rows.copy()
                
                cycle_event = {
                    "cycle": int(cycle),
                    "engines": []
                }

                for _, row in cycle_rows.iterrows():
                    cycle_event["engines"].append({
                        "engine_id": int(row["engine_id"]),

                        "ops": {
                            "op_1": float(row["op_1"]),
                            "op_2": float(row["op_2"]),
                            "op_3": float(row["op_3"]),
                        },

                        "sensors": {
                            f"sensor_{i}": float(row[f"sensor_{i}"])
                            for i in range(1,22)
                        }
                    })

                self.producer.send(INPUT_TOPIC, cycle_event) 
                time.sleep(config.interval)

        except Exception as e: 
            print(f"Error while producing datset: {e}")

        finally:
            self.producer.flush()
            stop_event.set()

