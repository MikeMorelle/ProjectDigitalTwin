import json, time
from kafka import KafkaProducer

from ml.data.load_data import load_data
from kafka_manager.stream_manager import ProducerConfig
from config import INPUT_TOPIC, KAFKA_BOOTSTRAP
from ml.features.sanitize_sensor_data import sanitize_sensors

#serialize message and encode it to bytes for sending via kafka
def serializer(message):
    return json.dumps(message).encode() 

class Producer:
    def __init__(self):
        #try to connect to kafka producer for 10 times with 5 seconds delay in between
        #not most beautiful solution but works for now
        for i in range(10):
            try:
                #Producer sends data to input topic for consumer to receive
                #bootstrap_servers -> list of kafka brokers to connect to (only one in this case, might be useful for scaling in the future)
                self.producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP, value_serializer=serializer)
                break
            except Exception as e: 
                print(f"Error initializing Kafka Producer in {i}th attempt.")
        #remember the faulty state to apply the fault injection/bias for given engine and sensor
        self.faulty_state = {}

    #get user config (dataset, interval, fault_config) and stream the data to kafka input topic
    #streaming is done in a separate thread (identified by run_id) to allow for stopping the streaming process via stop_event
    def stream(self, config: ProducerConfig, stop_event, run_id):
        try:  
            #returns dataset in pandas dataframe 
            df = load_data(config.dataset)
            
            #group the dataset by cycle 
            for cycle, cycle_rows in df.groupby("cycle", sort=True):
                
                #stop streaming if stop_event is set (via API call to /reset)
                if stop_event.is_set():
                    break   
                #meta info of current stream
                cycle_event = {
                    "run_id": run_id,
                    "dataset": config.dataset,
                    "cycle": int(cycle),
                    "engines": []
                }

                #process each row (engine) in current cycle
                for _, row in cycle_rows.iterrows():
                    #21 sensors in the dataset -> create a dict of sensor values
                    sensors = {
                        f"sensor_{i}": float(row[f"sensor_{i}"])
                        for i in range(1,22)
                    }

                    ops = {
                        f"op_setting_{i}": float(row[f"op_setting_{i}"])
                        for i in range(1,4)
                    }

                    #init faulty state for engine (if not already initialized) and apply bias to sensor values based on fault_config
                    self.init_faulty_engine_state(row["engine_id"],sensors)
                    sensors = self.bias_sensor_state((row["engine_id"]), sensors, config.fault_config)

                    #clean from NaN, None and non-float values -> replaces with 0.0 and prints a message to the console
                    sensors = sanitize_sensors(sensors)

                    #append the engine data to the cycle_event
                    cycle_event["engines"].append({
                        "engine_id": int(row["engine_id"]),

                        "ops": ops,

                        "sensors": sensors,
                        "true_rul": int(row["true_rul"])
                        
                    })

                #send the cycle_event to kafka input topic
                self.producer.send(INPUT_TOPIC, cycle_event) 
                #wait for the specified interval before sending the next cycle_event
                time.sleep(config.interval)

        except Exception as e: 
            print(f"Error while producing datset: {e}")

        finally:
            #flush the producer to ensure all messages are sent before stopping 
            self.producer.flush()
            #reset faulty state to avoid contamination from previous runs when a new run_id is received
            self.faulty_state = {}
            #might be redundant but ensures that the stop_event is set when the streaming process is done
            stop_event.set()

    #initialize the faulty state for the given engine_id with the initial sensor values -> applies bias consistently 
    def init_faulty_engine_state(self, engine_id, sensors):
        eid = int(engine_id)
        if eid not in self.faulty_state:
            self.faulty_state[eid] = sensors.copy()
    
    #apply the bias to the sensor values based on the fault_config for the given engine_id -> returns the biased sensor values
    def bias_sensor_state(self, engine_id, sensors, fault_config):
        eid = int(engine_id)

        offsets = self.faulty_state[eid]
        new_sensors = sensors.copy()

        #get the fault config for the given engine_id, if not found return an empty dict
        cfg = (fault_config or {}).get(str(eid), {})

        #apply the bias to the sensor values based on the fault_config -> currently offset and nan types of bias
        for sensor, rule in cfg.items():
            if sensor not in new_sensors:
                continue

            if rule["type"] == "nan":
                new_sensors[sensor] = float("nan")

        return new_sensors
    