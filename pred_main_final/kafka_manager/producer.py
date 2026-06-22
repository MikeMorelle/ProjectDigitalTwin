import json, time
from kafka import KafkaProducer, KafkaConsumer
from ml.data.load_data import load_data
from collections import defaultdict
from kafka_manager.event_builder import EngineState, compute_features
from kafka_manager.state_manager import ProducerConfig
from config import SENSORS, INPUT_TOPIC, KAFKA_BOOTSTRAP
import joblib

bundle = joblib.load("ml/models/latest/ano_model.joblib")
scaler = bundle["scalers"][1]

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

            engine_states = defaultdict(EngineState)
            
            for cycle, cycle_rows in df.groupby("cycle", sort=True):

                if stop_event.is_set():
                    break   

                cycle_rows = cycle_rows.copy()
                
                cycle_event = {
                    "cycle": int(cycle),
                    "engines": []
                }

                for _, row in cycle_rows.iterrows():
                    engine_id = int(row["engine_id"])
                    engine_state = engine_states[engine_id]

                    for s in SENSORS:
                        engine_state.data[s].append(float(row[s]))

                    features = compute_features(engine_state)

                    cycle_event["engines"].append({
                        "engine_id": int(engine_id),
                        "ops": {
                            "op1": float(row["op1"]),
                            "op2": float(row["op2"]),
                            "op3": float(row["op3"]),
                        },
                        "sensors": {
                            key: float(value) for key, value in features.items()
                        }
                    })

                self.producer.send(INPUT_TOPIC, cycle_event) 
                time.sleep(config.interval)

        except Exception as e: 
            print(f"Error while producing datset: {e}")

        finally:
            self.producer.flush()
            stop_event.set()

