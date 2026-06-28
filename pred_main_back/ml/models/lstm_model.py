from ml.models.base_model import PredictionModel
from ml.features.sequence_builder import SequenceBuilder
from ml.models.load_LSTM import load_LSTM_model
import pandas as pd
import torch
from config import SENSORS

class LSTMModel(PredictionModel):
    def __init__(self):
        (
            self.model,
            self.scaler,
            self.feature_cols,
            self.seq_length
        ) = load_LSTM_model()

        self.sequence = SequenceBuilder(self.seq_length)

    def predict(self, engine, dataset_num):
        engine_id = engine["engine_id"]
        current_ops = engine["ops"]
        current_sensors = engine["sensors"]


        ops_data = {
            "op_setting_1": current_ops["op_1"],
            "op_setting_2": current_ops["op_2"],
            "op_setting_3": current_ops["op_3"]
        }

        sensors_data = {s: current_sensors[s] for s in SENSORS}

        current_features = {**ops_data, **sensors_data}

        merged_df = pd.DataFrame([current_features], columns=self.feature_cols)

        scaled = self.scaler.transform(merged_df)
        scaled_df = pd.DataFrame(scaled, columns=self.feature_cols)

        X = self.sequence.transform(scaled_df, engine_id)

        self.model.eval() 

        with torch.no_grad():
            rul_prediction = self.model(X).item()

        return {
            "rul": float(rul_prediction)
        }
    
    def clear(self):
        self.sequence.clear()
