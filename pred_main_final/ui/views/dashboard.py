from db.db_client import fetch_latest_cycle_per_engine
from streamlit_autorefresh import st_autorefresh
import joblib
import pandas as pd
import shap
import numpy as np
import streamlit as st

st.set_page_config(page_title="Predictive Maintenance", layout="wide")
st.title("Live Anomaly Monitoring")
placeholder = st.empty()

#states
if "shutdown_engines" not in st.session_state:
    st.session_state.shutdown_engines = []

if "selected_engine" not in st.session_state:
    st.session_state.selected_engine = None

def get_status(score):
    if score == 1:
        return "Anomaly"
    else:
        return "Normal"

df = fetch_latest_cycle_per_engine()

if df.empty:
    with placeholder.container():
        st.warning("No data in database yet")
        st_autorefresh(interval=5000, key="dfrefresh")

else:
    rul_bundle = joblib.load("ml/models/latest/rul_model.joblib")
    rul_model = rul_bundle["rul_model"]

    ano_bundle = joblib.load("ml/models/latest/ano_model.joblib")
    ano_model = ano_bundle["model"]
    explainer = shap.TreeExplainer(ano_model)

    ops_df = df["ops"].apply(pd.Series)
    sensors_df = df["sensors"].apply(pd.Series)
    X = pd.concat([ops_df, sensors_df], axis=1)

    X = X.reindex(columns=rul_model.feature_names_in_)

    X = X.astype(float)

    df["rul"] = rul_model.predict(X)
    df["anomaly_score"] = ano_model.decision_function(X)
    df["top_factors"] = None
    anomaly_idx = df[df["anomaly_score"] < 0].index
    for i in anomaly_idx:
        sample = X.loc[[i]]
        shap_values = explainer.shap_values(sample)
        importance = pd.Series(np.abs(shap_values[0]), index=X.columns).sort_values(ascending=False)
        top3 = importance.head(3)
        df.at[i, "top_factors"] = list(top3.index)
    
    #add trend(current-mean) or z-score + summarize in sensor importance not only engine domain 

    total_anomalies = sum(df["anomaly_score"] < 0)

    st.dataframe(df)

    st.write(f"Amount of anomalies: {total_anomalies}")

    st_autorefresh(interval=15000, key="datarefresh")
