import pandas as pd, numpy as np
from collections import deque
from config import ROLLING_WINDOW_SIZE, SENSORS

class RollingFeatureBuilder:

    def __init__(self):
        self.window = ROLLING_WINDOW_SIZE
        self.buffers = {}

    def update(self, engine_id, sensors, ops):

        if engine_id not in self.buffers:
            self.buffers[engine_id] = deque(maxlen=self.window)

        self.buffers[engine_id].append(sensors)

        data = np.array(self.buffers[engine_id])

        features = {}

        for i, sensor in enumerate(SENSORS):

            features[f"{sensor}_roll_mean"] = data[:, i].mean()

            features[f"{sensor}_roll_std"] = (
                data[:, i].std()
                if len(data) > 1
                else np.nan
            )

        for op in ["op_1", "op_2", "op_3"]:
            features[op] = ops[op]

        return features