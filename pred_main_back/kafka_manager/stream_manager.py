import threading
from dataclasses import dataclass
import uuid

#own datastructure to hold the producer configuration consistently
@dataclass
class ProducerConfig: 
    dataset: str
    interval: int
    fault_config: dict 

class StreamManager:
    def __init__(self, producer):
        #producer is an instance of the Producer class, which handles the actual data streaming via Kafka
        #stop event is a threading event that allows for stopping the streaming process gracefully
        #thread is the thread that runs the streaming process, allowing it to run in the background
        #lock is a threading lock to ensure that the start and stop methods are thread-safe
        #run_id is a unique identifier for the current streaming session, allowing for tracking and managing multiple sessions
        #config holds the current producer configuration (dataset, interval, and fault configuration)
        self.producer = producer
        self.stop_event = threading.Event()
        self.thread = None
        self.lock = threading.Lock()

        self.run_id = None
        self.config = None

    def start(self, config): 
        #self.lock ensures that only one thread can execute the start method at a time
        with self.lock:
            #if already running -> False to indicate that the start request was not successful
            if self.is_running():
                return False
            
            #set thread params
            self.stop_event.clear()
            self.run_id = str(uuid.uuid4())
            self.config = config

            #start the producer thread with the given configuration and run_id
            #daemon=True ensures that the thread will not prevent the program from exiting if the main thread finishes execution
            self.thread = threading.Thread(
                target = self.producer.stream,
                args=(self.config, self.stop_event, self.run_id),
                daemon=True
            )

            self.thread.start()
            #signal that the start request was successful
            return True
        
    def stop(self):
        #self.lock ensures that only one thread can execute the stop method at a time
        with self.lock:
            #set the stop_event to signal the producer thread to stop streaming
            self.stop_event.set()

            #wait for the producer thread to finish execution before proceeding
            if self.thread:
                self.thread.join()

            self.thread = None
            self.run_id = None
            
    def is_running(self):
        #check if the producer thread is alive
        return self.thread and self.thread.is_alive()
    
    def status(self):
        return {
            "running": self.is_running(),
            "run_id": self.run_id,
            "dataset": self.config.dataset if self.config else None,
            "interval": self.config.interval if self.config else None,
            "bias": self.config.fault_config if self.config else None
        }