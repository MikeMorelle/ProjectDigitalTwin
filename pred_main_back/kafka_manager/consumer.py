import json, time
from kafka import KafkaConsumer

from db.db_client import get_connection, insert_batch
from config import INPUT_TOPIC, KAFKA_BOOTSTRAP
from ml.models.registry import ModelRegistry
from ml.models.prediction_service import PredictionService

class Consumer:
    def __init__(self):
        #try to connect to kafka consumer for 10 times with 5 seconds delay in between
        #not most beautiful solution but works for now
        for i in range(10):
            try:
                #Consumer listens to input topic and receives data from producer
                #bootstrap_servers -> list of kafka brokers to connect to (only one in this case, might be useful for scaling in the future)
                #auto_offset_reset -> where to start reading messages from (earliest = from the beginning of stream)
                #group_id -> unique identifier for the consumer group (only one in this case, might be useful for scaling in the future)
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
        #load all models from the model registry and initialize the prediction service with them
        models = ModelRegistry.load_models()
        self.prediction_service = PredictionService(models)
        #remember last run_id to reset the prediction service when a new run_id is received
        self.last_run_id = None

    def run(self):
        #connect to the database
        conn = get_connection()

        #always on: listening for incoming messages from producer
        for msg in self.consumer:
            #kpi: time for ML inference
            #start = time.perf_counter()
            #deserialize the message from kafka (bytes) to json
            data = json.loads(msg.value.decode("utf-8"))

            #reset to avoid contamination from previous runs when a new run_id is received
            if self.last_run_id != data["run_id"]:
                self.prediction_service.reset()
                self.last_run_id = data["run_id"]

            results = []

            cycle = data["cycle"]

            dataset_num = data["dataset"]

            #process each engine in the data
            for engine in data["engines"]:
                try:
                    #get prediction from registered models
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

            #kpi: time for ML inference
            #elapsed = time.perf_counter() - start
            #print(f"Time for ML inference: {elapsed}", flush=True)
            #insert results into database
            if results:
                insert_batch(conn, cycle, results)

#always run consumer
if __name__ == "__main__":
    consumer = Consumer()
    consumer.run()