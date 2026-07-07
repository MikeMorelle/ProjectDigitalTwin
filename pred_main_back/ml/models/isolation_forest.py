import joblib
import pandas as pd

from ml.models.base_model import PredictionModel
from ml.features.rolling_feature_builder import RollingFeatureBuilder
from config import SENSORS, OPS

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

        #if dataset_id in 2 or 4 -> use clustering to scale the sensor readings based on the cluster the engine belongs to
        if dataset_id in [2,4]:
            op_df = pd.DataFrame([engine["ops"]], columns=OPS)

            cluster = self.cluster_models[dataset_id].predict(op_df)[0]
            
            scaler = self.scaler[dataset_id][cluster]
            scaled = scaler.transform(sensors_df)

        #else use the scaler for the dataset directly
        else:
            scaled = self.scaler[dataset_id].transform(sensors_df)

        #update the rolling feature builder with the scaled sensor readings and ops to get the rolling mean and std features
        features = self.rolling.update(engine_id, scaled[0], engine["ops"])
                
        if features is None:
            print("Empty features", flush=True)
            return None

        #return a pandas dataframe with the features in the order of self.feature_cols to avoid naming issues during model inference
        return pd.DataFrame([[features[c] for c in self.feature_cols]], columns=self.feature_cols)

    #NOTE: IsoForest needs feature vector with >10 entries for correct detection...normally you could save resources and skip first 10 predictions. For visualiszing progress this is done in UI.
    def predict(self, engine, dataset_num):
        #build the feature vector for the given engine and dataset number
        X = self.build_feature_vector(engine, dataset_num)
        
        if X is None:
            print("Error while feature building")
            return None
        
        #get the anomaly score and prediction from the Isolation Forest model
        score = self.model.decision_function(X)[0]
        pred = self.model.predict(X)

        return {
            "anomaly_score": float(score),
            "is_anomaly": bool(pred==-1)
        }
    
    #clear to reset the rolling buffers for all engines -> used when starting a new run or calc shapiq values
    def clear(self):
        self.rolling.clear()