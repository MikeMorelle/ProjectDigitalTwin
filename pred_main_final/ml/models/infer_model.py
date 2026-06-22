import joblib
import pandas as pd
import shap

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

    # shap_values = explainer.shap_values(X)
    # contributions = pd.DataFrame({
    #     "feature": X.columns,
    #     "shap": shap_values[0]
    # })

    # pos = contributions[contributions["shap"]>0].sort_values("shap", ascending=False).head(3)
    # neg = contributions[contributions["shap"]<0].sort_values("shap", ascending=True).head(3)

    # top_contributions = pd.concat([pos,neg]).reset_index(drop=True)
    return rul