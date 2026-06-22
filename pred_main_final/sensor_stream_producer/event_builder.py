from collections import deque
import math
from config import SENSORS, ROLLING_WINDOW_SIZE

class EngineState:

    def __init__(self):
        self.data = {
            s: deque(maxlen=ROLLING_WINDOW_SIZE)
            for s in SENSORS
        }
        self.latest_cycle = 0
    
def compute_features(state):
    features = {}

    for s in SENSORS:
        values = state.data[s]

        if not values:
            continue

        values = [float(v) for v in values]
        
        n = len(values)
        mean = sum(values) / n
        
        if n > 1:
            var = sum(
                (x - mean)**2
                for x in values
            ) / (len(values) - 1)
            std = math.sqrt(var)
        else: 
            std = 0.0


        features[f"{s}_roll_mean"] = mean
        features[f"{s}_roll_std"] = std

    return features

