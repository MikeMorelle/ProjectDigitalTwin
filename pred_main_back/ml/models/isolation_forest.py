from ml.models.base_model import PredictionModel
from ml.features.rolling_feature_builder import RollingFeatureBuilder
import joblib
import pandas as pd
from config import SENSORS

class IsolationForestModel(PredictionModel):

    def __init__(self):
        bundle = joblib.load("ml/models/latest/ano_model.joblib")
        self.model = bundle["model"]
        self.scaler = bundle["scalers"]
        self.feature_cols = bundle["feature_cols"]
        self.rolling = RollingFeatureBuilder()

    def predict(self, engine, dataset_num):
        
        engine_id = engine["engine_id"]
        sensors_df = pd.DataFrame([[engine["sensors"][s] for s in SENSORS]], columns=SENSORS)

        if dataset_num == "FD001":
            scaled = self.scaler[1].transform(sensors_df)

        features = self.rolling.update(engine_id, scaled[0], engine["ops"])
                
        if features is None:
            print("Empty features", flush=True)
            return None

        X = pd.DataFrame([[features[c] for c in self.feature_cols]], columns=self.feature_cols)

        score = self.model.decision_function(X)[0]
        pred = self.model.predict(X)

        return {
            "anomaly_score": float(score),
            "is_anomaly": bool(pred==-1)
        }