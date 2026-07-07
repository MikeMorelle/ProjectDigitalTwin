from ml.models.lstm_model import LSTMModel
from ml.models.isolation_forest import IsolationForestModel

#register for all models used in the application, allowing for easy loading and management of models -> easily scalable
class ModelRegistry:
    @staticmethod
    def load_models():
        return [
            LSTMModel(),
            IsolationForestModel()
        ]
