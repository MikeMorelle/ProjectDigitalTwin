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
                    auto_offset_reset="latest",
                    group_id="anomaly-consumer"
                )
                break
            except Exception as e:
                print(f"Kafka consumer error at time step {i}:", e)
                time.sleep(5)

        self.iso_model = bundle["model"]
        self.iso_scaler = bundle["scalers"][1]
        self.iso_feature_cols = bundle["feature_cols"]
        self.loaded_model, self.loaded_scaler, self.lstm_feature_cols, self.lstm_seq_length = load_LSTM_model()
        self.sequence = SequenceBuilder(self.lstm_seq_length)
        self.rolling = RollingFeatureBuilder()

        self.stop_event = threading.Event()
    
    def run(self):

        conn = get_connection()

        for msg in self.consumer:

            if self.stop_event.is_set():
                break

            data = msg.value

            results = []

            cycle = data["cycle"]

            for engine in data["engines"]:
                engine_id = engine["engine_id"]

                current_ops = engine["ops"]
                current_sensors = engine["sensors"]


                ops_data = {
                    "op_setting_1": current_ops["op_1"],
                    "op_setting_2": current_ops["op_2"],
                    "op_setting_3": current_ops["op_3"]
                }

                sensors_data = {s: current_sensors[s] for s in SENSORS}

                current_features = {**ops_data, **sensors_data}

                merged_df = pd.DataFrame([current_features], columns=self.lstm_feature_cols)

                scaled = self.loaded_scaler.transform(merged_df)
                scaled_df = pd.DataFrame(scaled, columns=self.lstm_feature_cols)

                X = self.sequence.transform(scaled_df, engine_id)

                self.loaded_model.eval() 
                with torch.no_grad():
                    rul_prediction = self.loaded_model(X).item()

                #############################

                sensors_df = pd.DataFrame([[engine["sensors"][s] for s in SENSORS]], columns=SENSORS)

                scaled = self.iso_scaler.transform(sensors_df)

                features = self.rolling.update(engine_id, scaled[0], engine["ops"])
                
                if features is None:
                    print("Empty features", flush=True)
                    continue

                X = pd.DataFrame([[features[c] for c in self.iso_feature_cols]], columns=self.iso_feature_cols)

                score = self.iso_model.decision_function(X)[0]
                pred = self.iso_model.predict(X)

                results.append({
                    "engine_id": engine_id,
                    "cycle": cycle,
                    "ops": engine["ops"],
                    "sensors": engine["sensors"],
                    "anomaly_score": float(score),
                    "is_anomaly": bool(pred==-1),
                    "rul": rul_prediction
                })

            insert_batch(conn, data["cycle"], results)

if __name__ == "__main__":
    consumer = Consumer()
    consumer.run()