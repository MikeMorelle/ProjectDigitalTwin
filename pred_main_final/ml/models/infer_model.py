import joblib
import pandas as pd

#für ano model lösche get_alert_level
bundle = joblib.load("ml/models/latest/ano_model.joblib") 
model = bundle["model"] 

def predict_anomaly(df):
    score = model.decision_function(df)[0]
    pred = model.predict(df)[0]
    
    return score, pred