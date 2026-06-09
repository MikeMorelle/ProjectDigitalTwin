import json, time
from kafka import KafkaProducer, KafkaConsumer
from ml.data.load_data import load_data
from collections import defaultdict
from event_builder import EngineState, compute_features
from config import SENSORS, PROD_SLEEP_SECONDS, INPUT_TOPIC


#PRODUCER
def create_producer():
    producer = None
    while producer is None:
        try:
            producer = KafkaProducer(bootstrap_servers="kafka:9092", value_serializer=lambda v: json.dumps(v).encode("utf-8"))
        except Exception as e:
            print("KAFKA ERROR:", e)
            time.sleep(5)
    return producer

def main():
    df = load_data()

    producer = create_producer()

    engine_states = defaultdict(EngineState)
    
    for cycle in sorted(df["cycle"].unique()):
        cycle_event = {
            "cycle": int(cycle),
            "engines": []
        }
        cycle_rows = df[df["cycle"] == cycle]

        for _, row in cycle_rows.iterrows():
            engine_id = int(row["engine_id"])
            state = engine_states[engine_id]

            for s in SENSORS:
                state.data[s].append(float(row[s]))

            features = compute_features(state)

            cycle_event["engines"].append({
                "engine_id": int(engine_id),
                **features
            })

        producer.send(INPUT_TOPIC, cycle_event) 
        producer.flush()
        time.sleep(PROD_SLEEP_SECONDS)

if __name__ == "__main__":
    main()

