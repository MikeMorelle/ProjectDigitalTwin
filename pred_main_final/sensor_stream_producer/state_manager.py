import threading

class AppState:
    def __init__(self):
        self.lock = threading.Lock()
        self.running = threading.Event()
        self.current_id = None
        self.current_ds = None
        self.current_thread = None
        self.interval = None

state = AppState()
