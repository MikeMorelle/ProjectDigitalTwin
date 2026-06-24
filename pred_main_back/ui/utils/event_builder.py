# state_manager.py
from collections import defaultdict, deque
import numpy as np

class EngineState:
    def __init__(self, seq_len=30, roll_window=10):
        self.seq_len = seq_len
        self.roll_window = roll_window

        self.sequence = deque(maxlen=seq_len)
        self.rolling = defaultdict(lambda: deque(maxlen=roll_window))

        self.latest_cycle = 0

    def update(self, cycle: int, sensors: dict):
        if cycle <= self.latest_cycle:
            return False

        self.latest_cycle = cycle

        vec = list(sensors.values())
        

        for k, v in sensors.items():
            self.rolling[k].append(v)
            self.sequence.append(vec)

        return True

def build_features(state, sensors, ops):
    features = {}

    # raw sensors
    for k, v in sensors.items():
        features[k] = v

        arr = np.array(state.rolling[k])

        if len(arr) > 0:
            features[f"{k}_roll_mean"] = arr.mean()
            features[f"{k}_roll_std"] = arr.std()
        else:
            features[f"{k}_roll_mean"] = 0.0
            features[f"{k}_roll_std"] = 0.0

    # ops
    features.update(ops)

    return features

class StateManager:
    def __init__(self):
        self.engines = {}

    def get(self, engine_id: int) -> EngineState:
        if engine_id not in self.engines:
            self.engines[engine_id] = EngineState()
        return self.engines[engine_id]
    
# ml_pipeline.py
import numpy as np
import pandas as pd

class AnomalyPipeline:
    def __init__(self, model, scaler, feature_cols):
        self.model = model
        self.scaler = scaler
        self.feature_cols = feature_cols

    def predict(self, features: dict):
        X = pd.DataFrame([features])[self.feature_cols]
        return float(self.model.decision_function(X)[0])


class LSTMPipeline:
    def __init__(self, model, scaler, feature_cols, seq_len):
        self.model = model
        self.scaler = scaler
        self.feature_cols = feature_cols
        self.seq_len = seq_len

    def predict(self, state):
        if len(state.sequence) < self.seq_len:
            return None

        seq = np.array(state.sequence)

        seq_df = pd.DataFrame(seq, columns=self.feature_cols)
        seq_scaled = self.scaler.transform(seq_df)

        seq_scaled = seq_scaled.reshape(1, self.seq_len, len(self.feature_cols))

        return float(self.model.predict(seq_scaled, verbose=0)[0][0])


class PredictionEngine:
    def __init__(self, anomaly_pipe, lstm_pipe):
        self.anomaly_pipe = anomaly_pipe
        self.lstm_pipe = lstm_pipe

    def predict(self, state, features: dict):
        return {
            "anomaly_score": self.anomaly_pipe.predict(features),
            "lstm_rul": self.lstm_pipe.predict(state)
        }