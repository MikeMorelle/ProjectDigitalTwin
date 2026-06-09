import joblib
import pandas as pd

#für ano model lösche get_alert_level
model = joblib.load("ml/models/latest/iforest.pkl") 
scaler = joblib.load("ml/models/latest/scaler.pkl")

def predict_anomaly(df):
    x_scaled = scaler.transform(df)
    score = model.decision_function(x_scaled)[0]
    pred = model.predict(x_scaled)[0]
    
    return score, pred