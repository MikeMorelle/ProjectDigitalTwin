import joblib
import pandas as pd

#für ano model lösche get_alert_level
bundle = joblib.load("ml/models/latest/ano_model.joblib") 
model = bundle["model"] 

bundle2 = joblib.load("ml/models/latest/rul_model.joblib")
rul_model = bundle2["rul_model"]

def predict_anomaly(df):
    score = model.decision_function(df)[0]
    pred = model.predict(df)[0]
    
    return score, pred

def predict_rul(X):
    rul = rul_model.predict(X)[0]
    return rul