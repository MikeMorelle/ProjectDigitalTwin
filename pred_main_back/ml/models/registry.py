from ml.models.lstm_model import LSTMModel
from ml.models.isolation_forest import IsolationForestModel

class ModelRegistry:

    @staticmethod
    def load_models():
        return [
            LSTMModel(),
            IsolationForestModel()
        ]
