import numpy as np
from collections import deque
import joblib

from config import SENSORS, OPS

class RollingFeatureBuilder:

    def __init__(self):
        #window size (determined during model training) for rolling mean and std calculation
        self.window = joblib.load("ml/models/latest/ano_model.joblib")["rolling_window"]
        #buffer for each engine_id to store the last window number of sensor readings
        self.buffers = {}

    def update(self, engine_id, sensors, ops):
        #check if buffer exists for the engine_id, if not create a new deque with maxlen=window
        if engine_id not in self.buffers:
            self.buffers[engine_id] = deque(maxlen=self.window)

        #append the new sensor readings to the buffer for the engine_id
        self.buffers[engine_id].append(sensors)

        #merges arrays to create a 2D numpy array for rolling calculations -> shape: (window, num_sensors) -> better tahn np.array as error if lenght inconsistencies
        data = np.stack(self.buffers[engine_id])

        features = {}

        #calculate rolling mean and std for each sensor using the current data in the buffer
        for i, sensor in enumerate(SENSORS):
            
            features[f"{sensor}_roll_mean"] = data[:, i].mean()

            #if only 1 value in buffer -> std = 0.0 as in model training
            features[f"{sensor}_roll_std"] = (
                data[:, i].std()
                if len(data) > 1
                else 0.0
            )
        #nothing for ops -> just add them to the feature vector
        for op in OPS:
            features[op] = ops[op]

        return features
    
    #clear to reset the rolling buffers for all engines -> used when starting a new run or calc shapiq values
    def clear(self):
        self.buffers = {}