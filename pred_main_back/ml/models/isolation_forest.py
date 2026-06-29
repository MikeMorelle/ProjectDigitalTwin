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
        self.cluster_models = bundle["cluster_models"]
        self.rolling = RollingFeatureBuilder()

    def build_feature_vector(self, engine, dataset_num):
                
        engine_id = engine["engine_id"]
        sensors_df = pd.DataFrame([[engine["sensors"][s] for s in SENSORS]], columns=SENSORS)

        dataset_id = int(dataset_num.replace("FD",""))

        if dataset_id in [2,4]:
            op_df = pd.DataFrame([engine["ops"]], columns=["op_1", "op_2", "op_3"])

            cluster = self.cluster_models[dataset_id].predict(op_df)[0]
            
            scaler = self.scaler[dataset_id][cluster]
            scaled = scaler.transform(sensors_df)

        else:
            scaled = self.scaler[dataset_id].transform(sensors_df)

        features = self.rolling.update(engine_id, scaled[0], engine["ops"])
                
        if features is None:
            print("Empty features", flush=True)
            return None

        return pd.DataFrame([[features[c] for c in self.feature_cols]], columns=self.feature_cols)

    def predict(self, engine, dataset_num):

        X = self.build_feature_vector(engine, dataset_num)
        
        if X is None:
            print("Error while feature building")
            return None
        
        score = self.model.decision_function(X)[0]
        pred = self.model.predict(X)

        return {
            "anomaly_score": float(score),
            "is_anomaly": bool(pred==-1)
        }
    
    def clear(self):
        self.rolling.clear()