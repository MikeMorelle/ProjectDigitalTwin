from abc import ABC, abstractmethod

class PredictionModel(ABC):
    @abstractmethod
    def predict(self, engine_data: dict):
        pass