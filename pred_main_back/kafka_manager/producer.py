import json, time
from kafka import KafkaProducer, KafkaConsumer
from ml.data.load_data import load_data
from kafka_manager.state_manager import ProducerConfig
from config import SENSORS, INPUT_TOPIC, KAFKA_BOOTSTRAP
from ml.features.sanitize_sensor_data import sanitize_sensors

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

        self.faulty_state = {}

    def stream(self, config: ProducerConfig, stop_event, run_id):
        try:    
            df = load_data(config.dataset)
            
            for cycle, cycle_rows in df.groupby("cycle", sort=True):

                if stop_event.is_set():
                    break   

                cycle_event = {
                    "run_id": run_id,
                    "dataset": config.dataset,
                    "cycle": int(cycle),
                    "engines": []
                }

                for _, row in cycle_rows.iterrows():
                    sensors = {
                        f"sensor_{i}": float(row[f"sensor_{i}"])
                        for i in range(1,22)
                    }

                    self.init_faulty_engine_state(row["engine_id"],sensors)
                    sensors = self.bias_sensor_state((row["engine_id"]), sensors, config.fault_config)

                    sensors = sanitize_sensors(sensors)

                    cycle_event["engines"].append({
                        "engine_id": int(row["engine_id"]),

                        "ops": {
                            "op_1": float(row["op_1"]),
                            "op_2": float(row["op_2"]),
                            "op_3": float(row["op_3"]),
                        },

                        "sensors": sensors,
                        "true_rul": int(row["true_rul"])
                        
                    })

                self.producer.send(INPUT_TOPIC, cycle_event) 
                
                time.sleep(config.interval)

        except Exception as e: 
            print(f"Error while producing datset: {e}")

        finally:
            self.producer.flush()
            self.faulty_state = {}
            stop_event.set()

    def init_faulty_engine_state(self, engine_id, sensors):
        eid = int(engine_id)
        if eid not in self.faulty_state:
            self.faulty_state[eid] = sensors.copy()
        
    def bias_sensor_state(self, engine_id, sensors, fault_config):
        eid = int(engine_id)

        offsets = self.faulty_state[eid]
        new_sensors = sensors.copy()

        cfg = (fault_config or {}).get(str(eid), {})

        for sensor, rule in cfg.items():
            if sensor not in new_sensors:
                continue

            if rule["type"] == "offset":
                offsets[sensor] += rule["value"]
                new_sensors[sensor] += offsets[sensor]

            if rule["type"] == "nan":
                new_sensors[sensor] = float("nan")
        
        return new_sensors
    