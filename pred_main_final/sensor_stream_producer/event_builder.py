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
        values = list(state.data[s])

        if len(values) == 0:
            continue

        mean = sum(values) / len(values)
        if len(values) == 1:
            std = 0

        else: 
            var = sum(
                (x - mean)**2
                for x in values
            ) / (len(values) - 1)
            std = math.sqrt(var)

        features[f"{s}_roll_mean"] = mean
        features[f"{s}_roll_std"] = std

    return features

