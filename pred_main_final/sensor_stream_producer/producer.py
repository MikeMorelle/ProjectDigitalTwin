import json, time
from kafka import KafkaProducer, KafkaConsumer
from ml.data.load_data import load_data
from collections import defaultdict
from sensor_stream_producer.event_builder import EngineState, compute_features
from config import SENSORS, INPUT_TOPIC, KAFKA_BOOTSTRAP
import joblib
from sensor_stream_producer.state_manager import state

bundle = joblib.load("ml/models/latest/ano_model.joblib")
scaler = bundle["scalers"][1]


class KafkaProducerSingleton:
    instance = None

    @classmethod
    def get(cls):
        if cls.instance is None:
            try:
                cls.instance = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP, value_serializer=lambda v: json.dumps(v).encode("utf-8"))
            except Exception as e:
                print("ERROR during Kafka Prod", e)

        return cls.instance

def produce_dataset(ds_name:str, interval: int):

    try:
        df = load_data(ds_name)

        producer = KafkaProducerSingleton.get()

        engine_states = defaultdict(EngineState)
        
        for cycle, cycle_rows in df.groupby("cycle", sort=True):

            if not state.running.is_set():
                break   #stop if no event

            cycle_rows = cycle_rows.copy()

            cycle_rows[SENSORS] = scaler.transform(cycle_rows[SENSORS].astype(float))
            
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

            producer.send(INPUT_TOPIC, cycle_event) 
            time.sleep(interval)

    except Exception as e: 
        print(f"Error while producing datset: {e}")

    finally:
        state.running.clear()

