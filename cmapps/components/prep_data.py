import joblib
import numpy as np
import pandas as pd

def get_status(rul):
        if rul < 30:
            return "Critical"
        elif rul < 60:
            return "Warning"
        else:
            return "OK"

def get_stats(df):

    try:
        model = joblib.load("models/xgb_rul_model.pkl")
        scaler = joblib.load("models/scaler.pkl")
        feature_cols = joblib.load("models/features.pkl")

    except:
        print("Train a model first")

    RUL_MAX = 125 

    df = df.sort_values(["unit_num", "cycle"])

    latest = df.groupby("unit_num").head(1)
    latest = latest.groupby("unit_num").mean().reset_index()

    X = latest.reindex(columns=feature_cols)

    X_scaled = scaler.transform(X)

    preds = model.predict(X_scaled)

    latest["pred_RUL"] = preds

    latest['health_score'] = np.clip(
        latest["pred_RUL"] / RUL_MAX * 100,
        0,
        100 
    )

    latest["failure_prob"] = np.clip(
        1 - (latest["pred_RUL"] / RUL_MAX),
        0,
        1
    )
        
    latest["status"] = latest["pred_RUL"].apply(get_status)
    

    sensor_cols = [c for c in latest.columns if "sensor" in c]

    return latest, sensor_cols, X_scaled

def add_remaining_useful_life(df):

    n_cycles = df.groupby("unit_num")["time_cycles"].max()

    df = df.copy()

    df = df.merge(
        n_cycles.rename("n_cycles"),
        left_on="unit_num",
        right_index=True
    )

    df["RUL"] = df["n_cycles"] - df["time_cycles"]

    df = df.drop("n_cycles", axis=1)

    return df

def feature_selection(data):
    #manually selected by plot behavior
    del_cols = ["sensor2", "sensor3", "sensor4","sensor7","sensor8", "sensor9", "sensor11", "sensor12", "sensor13", "sensor15", "sensor17", "sensor20", "sensor21"]
    data = data.drop(del_cols, axis=1)

    #automatic filter with mid results
    #low_var_cols = [c for c in train.columns if train[c].std() < 1e-3]

    return data

def split_data(train, test, y_test):
    X_train = train.drop(
        ["unit_num","time_cycles", "RUL"],
        axis=1
        )

    y_train = train["RUL"]

    test_last = test.groupby("unit_num").last().reset_index()

    X_test = test_last.drop(
        ["unit_num", "time_cycles"],
        axis=1
    )

    y_test = y_test.iloc[:,0]

    return X_train, y_train, X_test, y_test