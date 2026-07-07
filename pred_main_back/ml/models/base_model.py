from abc import ABC, abstractmethod

#abstract base class for prediction models -> all have predict method to be implemented
class PredictionModel(ABC):
    @abstractmethod
    def predict(self, engine_data: dict):
        pass