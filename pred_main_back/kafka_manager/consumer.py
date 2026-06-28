import json, time
from kafka import KafkaConsumer
from db.db_client import get_connection, insert_batch
from config import INPUT_TOPIC, KAFKA_BOOTSTRAP, SENSORS
from ml.features.rolling_feature_builder import RollingFeatureBuilder
from ml.features.sequence_builder import SequenceBuilder
import joblib
import numpy as np, pandas as pd
import threading, torch
from ml.models.load_LSTM import load_LSTM_model
from ml.models.registry import ModelRegistry
from ml.models.prediction_service import PredictionService
from kafka_manager.state_manager import StreamManager

def deserializer(value):
    if value is None:
        return
    
    try:
        return json.loads(value.decode('utf-8'))
    except Exception as e:
        print("Unable to decode", e, flush=True)
        return None

bundle = joblib.load("ml/models/latest/ano_model.joblib")   

class Consumer:
    def __init__(self):
        for i in range(10):
            try:
                self.consumer = KafkaConsumer(
                    INPUT_TOPIC,
                    bootstrap_servers=KAFKA_BOOTSTRAP,
                    value_deserializer=deserializer,
                    auto_offset_reset="earliest",
                    group_id=f"anomaly-consumer"
                )
                break
            except Exception as e:
                print(f"Kafka consumer error at time step {i}:", e)
                time.sleep(5)

        models = ModelRegistry.load_models()

        self.prediction_service = PredictionService(models)

        self.last_run_id = None

    def run(self):

        conn = get_connection()

        for msg in self.consumer:
            #start = time.perf_counter()

            data = msg.value

            if self.last_run_id != data["run_id"]:
                self.prediction_service.reset()
                self.last_run_id = data["run_id"]

            results = []

            cycle = data["cycle"]

            dataset_num = data["dataset"]

            for engine in data["engines"]:
                try:

                    prediction = (
                        self.prediction_service.predict(engine, dataset_num)
                    )

                    results.append({
                        "run_id": data["run_id"],
                        "engine_id": engine["engine_id"],
                        "cycle": cycle,
                        "ops": engine["ops"],
                        "sensors": engine["sensors"],
                        **prediction
                    })

                except Exception as e:
                    print(f"ML failed: {e}")

            #elapsed = time.perf_counter() - start
            #print(f"Time for ML inference: {elapsed}", flush=True)

            if results:
                insert_batch(conn, cycle, results)

if __name__ == "__main__":
    consumer = Consumer()
    consumer.run()