import threading
from dataclasses import dataclass
import uuid

@dataclass
class ProducerConfig: 
    dataset: str
    interval: int

class StreamManager:
    def __init__(self, producer):
        self.producer = producer
        self.stop_event = threading.Event()
        self.thread = None
        self.lock = threading.Lock()

        self.run_id = None
        self.config = None

    def start(self, config): 
        with self.lock:
            if self.is_running():
                return False
            
            self.stop_event.clear()

            self.run_id = str(uuid.uuid4())
            self.config = config

            self.thread = threading.Thread(
                target = self.producer.stream,
                args=(config, self.stop_event, self.run_id),
                daemon=True
            )

            self.thread.start()
        
            return True
        
    def stop(self):
        with self.lock:
            self.stop_event.set()

            if self.thread:
                self.thread.join()

            self.thread = None
            self.run_id = None
            
    def is_running(self):
        return self.thread and self.thread.is_alive()
    
    def status(self):
        return {
            "running": self.is_running(),
            "run_id": self.run_id,
            "dataset": self.config.dataset if self.config else None,
            "interval": self.config.interval if self.config else None
        }

