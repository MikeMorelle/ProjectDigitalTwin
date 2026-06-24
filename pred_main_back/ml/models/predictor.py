from abc import ABC, abstractmethod
from tensorflow.keras.models import load_model
import joblib, json
from ml.features.sequence_builder import SequenceBuilder
from ml.features.rolling_feature_builder import RollingFeatureBuilder
import torch

rul_bundle=joblib.load("ml/models/latest/lstm_meta.joblib")
ano_bundle=joblib.load("ml/models/latest/ano_model.joblib")

def load_LSTM(device="cpu"):
    dir = "ml/models/latest/"
    with open(f"{dir}/config.json") as f:
        config = json.load(f)

    scaler = joblib.load("f{dir}/scaler.pkl")


    model = LSTMModel(
        input_size=config["input_size"],
        hidden_size=config["hidden_size"],
        num_layers=config["num_layers"],
        dropout=config["dropout"],
    ).to(device)

    
    model.load_state_dict(
        torch.load(f"{dir}/model_state_dict.pth",
                   map_location=device)
    )

    model.eval()

    return model, scaler, config


#strategy pattern
class Predictor(ABC):
    @abstractmethod
    def predict(self, history_df):
        pass

class RULPredictor(Predictor):
    def __init__(self):
        self.device = "cpu"
        self.model = load_model("ml/models/latest/lstm_rul.keras")
        self.scaler = rul_bundle["scaler"]
        self.sequence_builder = (SequenceBuilder())
    
    def predict(self, history_df):
        sequence = (self.sequence_builder.transform(history_df))

        og_shape = sequence.shape

        scaled = self.scaler.transform(
            sequence.reshape(-1, sequence.shape[-1])
        )

        scaled = scaled.reshape(og_shape)

        prediction = (self.model.predict(scaled, verbose=0)[0][0])

        return {
            "rul": float(prediction)
        }
    
class AnomalyPredictor(Predictor):
    def __init__(self):
        self.model = ano_bundle["model"]
        self.scaler = ano_bundle["scalers"][1]  #adapt to dataset
        self.feature_builder = (RollingFeatureBuilder())

    def predict(self, history_df):
        features = (self.feature_builder.transform(history_df))

        scaled = (self.scaler.transform(features))

        score = (self.model.decision_function(scaled)[0])

        anomaly = (self.model.predict(scaled)[0])

        return {
            "anomaly_score": float(score),
            "is_anomaly": anomaly == -1
        }