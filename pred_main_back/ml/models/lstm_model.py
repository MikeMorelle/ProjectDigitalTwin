import pandas as pd
import torch

from ml.models.base_model import PredictionModel
from ml.features.sequence_builder import SequenceBuilder
from ml.models.load_LSTM import load_LSTM_model
from config import SENSORS, OPS

class LSTMModel(PredictionModel):
    def __init__(self):
        (
            self.model,
            self.scaler,
            self.feature_cols,
            self.seq_length
        ) = load_LSTM_model()

        self.sequence = SequenceBuilder(self.seq_length)

    #NOTE: LSTM needs sequence with >50 entries for correct estimation...normally you could save resources and skip first 50 predictions. For visualiszing progress this is done in UI.
    def predict(self, engine, dataset_num): #dataset_num is not used for LSTM, but kept for consistency with other models
        engine_id = engine["engine_id"]
        current_ops = engine["ops"]
        current_sensors = engine["sensors"]

        #rename ops and sensors to match the feature columns used during model training
        ops_data = {o: current_ops[o] for o in OPS}

        sensors_data = {s: current_sensors[s] for s in SENSORS}

        #merge ops and sensors into a single feature vector with cols names matching the feature columns used during model training
        current_features = {**ops_data, **sensors_data}
        merged_df = pd.DataFrame([current_features], columns=self.feature_cols)

        #scale
        scaled = self.scaler.transform(merged_df)
        scaled_df = pd.DataFrame(scaled, columns=self.feature_cols)

        #transform the scaled feature vector into a sequence of feature vectors for the engine_id
        X = self.sequence.transform(scaled_df, engine_id)

        #perform inference with the LSTM model to predict the RUL (Remaining Useful Life) for the engine_id
        with torch.no_grad():
            rul_prediction = self.model(X).item()

        return {
            "rul": float(rul_prediction)
        }
    
    #clear to reset the history buffers for all engines -> used when starting a new run or calc shapiq values
    def clear(self):
        self.sequence.clear()
