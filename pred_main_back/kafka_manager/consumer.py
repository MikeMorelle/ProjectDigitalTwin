import json, time
from kafka import KafkaConsumer
from db.db_client import get_connection, insert_batch
from config import INPUT_TOPIC, KAFKA_BOOTSTRAP
import joblib

from ml.models.registry import ModelRegistry
from ml.models.prediction_service import PredictionService

class Consumer:
    def __init__(self):
        for i in range(10):
            try:
                self.consumer = KafkaConsumer(
                    INPUT_TOPIC,
                    bootstrap_servers=KAFKA_BOOTSTRAP,
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

            data = json.loads(msg.value.decode("utf-8"))

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
                        "true_rul": engine["true_rul"],
                        **prediction,
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