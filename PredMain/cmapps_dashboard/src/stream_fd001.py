import pandas as pd 
import time
import joblib
from datetime import datetime

from feature_engineering import build_window_features, WINDOW
from shap_engine import ShapEngine

#Load data
index_names = ['unit_num', 'time_cycles']
setting_names = ['setting1', 'setting2', 'setting3']
sensor_names = ['sensor{}'.format(i) for i in range(1, 22)]
col_names = index_names + setting_names + sensor_names
train = pd.read_csv("cmapps_dashboard/data/train_FD001.txt", sep='\s+', header=None, names=col_names)

#Load model and SHAP engine
model = joblib.load("cmapps_dashboard/models/rul_model.pkl")
shap= ShapEngine(model)

#history list to store predictions and SHAP values over time
history = []
#only process one engine for demonstration purposes
engine_id = 1
eng = train[train["unit_num"] == engine_id]

#Load the feature columns used by the model
features = joblib.load("cmapps_dashboard/models/feat_cols.pkl")

#Simulate real-time data processing by iterating through the sensor data with a rolling window
for i in range(WINDOW, len(eng)):

    #Extract the current window of sensor data and build features
    window = eng.iloc[i-WINDOW:i]
    row = build_window_features(window)

    #Create a DataFrame for the latest features and ensure it has all the columns expected by the model
    X_live = pd.DataFrame([row])
    for col in features:
        if col not in X_live.columns:
            X_live[col] = 0
    X_live = X_live[features]  

    #Predict RUL and SHAP values    
    pred_rul = model.predict(X_live)[0]
    top_features = shap.explain(X_live)

    #Store the results in history and save to CSV
    output = {
        "engine_id": engine_id,
        "time": datetime.now().isoformat(),
        "predicted_rul": pred_rul,
        "top_features": top_features.to_dict(),
    }

    #optional
    output.update(X_live.iloc[0].to_dict())

    #Append the output to history and save to CSV
    history.append(output)

    #Save history to CSV after each prediction
    pd.DataFrame(history).to_csv("cmapps_dashboard/output/history.csv", index=False)
    print(f"Engine {engine_id} at time {i}: Predicted RUL = {pred_rul}")
    
    #Sleep to simulate real-time processing 
    time.sleep(2)


