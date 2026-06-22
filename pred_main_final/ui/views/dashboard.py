from db.db_client import fetch_latest_cycle_per_engine, fetch_engine_history # fetch_engine_history  – to get all cycles of one engine for trend charts
from streamlit_autorefresh import st_autorefresh
import joblib
import pandas as pd
import shap
import numpy as np
import streamlit as st
from ml.data.load_data import load_data # to read the raw NASA sensor file
import requests # to ask the API which dataset is active

#
#DONT FORGET SCALING
#

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

# ============================================================
# ADDITION 1: Helper functions for raw sensor data
# These load the original NASA text files so we can show
# real physical sensor values (not processed features).
# ============================================================

def get_current_dataset():
    """
    Ask the FastAPI service which dataset is currently streaming.
    If the API is unavailable, fall back to 'FD001'.
    """
    try:
        resp = requests.get("http://api:8000/status", timeout=2)
        data = resp.json()
        return data.get("dataset", "FD001")
    except:
        return "FD001"

@st.cache_data
def get_raw_data(ds_name=None):
    """
    Load the raw NASA dataset ONCE and cache it in memory.
    ds_name: which dataset to load (e.g. 'FD001', 'FD002').
    If not given, we auto‑detect from the API.
    """
    if ds_name is None:
        ds_name = get_current_dataset()
    return load_data(ds_name)

def get_engine_raw_sensors(engine_id):
    """
    From the raw dataset, extract only the sensor columns
    (sensor_1, sensor_2, … sensor_21) plus the cycle number
    for one specific engine. Sorted from oldest to newest cycle.
    """
    df = get_raw_data()                                    # get the cached dataset
    eng_df = df[df["engine_id"] == int(engine_id)].copy()  # keep only one engine
    sensor_cols = [c for c in eng_df.columns if c.startswith("sensor_")]  # find sensor columns
    return eng_df[["cycle"] + sensor_cols].sort_values("cycle")           # return cycle + sensors

# ============================================================
# ADDITION 2: Dialog – shown when an engine card is clicked (POP UP)
# ============================================================

@st.dialog("Engine Detail", width="large")
def show_engine_detail(engine_data):
    """
    Show full details for one engine.
    engine_data is one row from our main DataFrame,
    which already has anomaly_score, rul, status, and top_factors.
    """
    eng = engine_data["engine_id"]

    # ---- Basic info ----
    st.header(f"Engine {eng} Detail Report")

    # ---- Three KPI cards ----
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Cycle", engine_data["cycle"])
    with col2:
        st.metric("Anomaly Score", f"{engine_data['anomaly_score']:.2f}")
    with col3:
        rul_value = engine_data["rul"]
        if not np.isnan(rul_value):
            st.metric("Remaining Useful Life (RUL)", f"{rul_value:.0f} cycles")
        else:
            st.metric("Remaining Useful Life (RUL)", "N/A")

    # ---- Maintenance recommendation ----
    st.subheader("Maintenance Recommendation")
    score = engine_data["anomaly_score"]
    if score < -1.0:
        st.error("🔴 Critical — Immediate inspection recommended.")
    elif score < 0:
        st.warning("🟡 Warning — Schedule maintenance within next cycles.")
    else:
        st.success("🟢 Normal — Engine operating normally.")

    # ---- Top Contributing Factors (SHAP explanation) ----
    top_factors = engine_data.get("top_factors", [])
    if top_factors:
        st.subheader("Top Contributing Factors")
        for i, factor in enumerate(top_factors, 1):
            st.write(f"{i}. {factor}")

    # ---- Historical Trends (anomaly score & RUL over all cycles) ----
    st.subheader("Trends Over Time")
    history = fetch_engine_history(eng)        # get all cycles from the database
    if not history.empty:
        # compute_predictions is defined later in the main block,
        # because it needs the loaded models. We'll call it now.
        history = compute_predictions(history)  # add anomaly_score & rul columns
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.line_chart(history.set_index("cycle")["anomaly_score"], use_container_width=True)
            st.caption("Anomaly Score per Cycle")
        with chart_col2:
            st.line_chart(history.set_index("cycle")["rul"], use_container_width=True)
            st.caption("RUL per Cycle (higher = more life left)")

    # ---- Raw Sensor Trends (real physical values from the NASA file) ----
    st.subheader("Sensor Trends (Raw Values)")
    raw = get_engine_raw_sensors(eng)
    if raw.empty:
        st.info("No raw sensor data for this engine.")
    else:
        all_sensors = [c for c in raw.columns if c != "cycle"]
        default_sensors = all_sensors[:3]  # pre‑select the first three sensors
        selected = st.multiselect(
            "Select sensors to display",
            all_sensors,
            default=default_sensors,
            key=f"sensors_{eng}"           # unique key per engine
        )
        if selected:
            chart_data = raw.set_index("cycle")[selected]
            st.line_chart(chart_data, use_container_width=True)

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
    
    # ============================================================
    # ADDITION 3: compute status from anomaly score
    # (instead of the old get_status function which used is_anomaly)
    # ============================================================
    df["status"] = df["anomaly_score"].apply(lambda x: "Anomaly" if x < 0 else "Normal")

    # ============================================================
    # ADDITION 4: define compute_predictions HERE inside Engine detail (POP UP),
    # because it needs the loaded models (rul_model, ano_model)
    # ============================================================
    def compute_predictions(history_df):
        """
        Take a DataFrame with raw 'ops' and 'sensors' JSON columns
        (from the database) and run the ML models on every row.
        Returns the same DataFrame with two new columns:
        - anomaly_score  (lower = more anomalous)
        - rul            (Remaining Useful Life, in cycles)
        """
        ops_df = history_df["ops"].apply(pd.Series)
        sensors_df = history_df["sensors"].apply(pd.Series)
        X = pd.concat([ops_df, sensors_df], axis=1)
        X = X.reindex(columns=rul_model.feature_names_in_)
        X = X.astype(float)

        result = history_df.copy()
        result["anomaly_score"] = ano_model.decision_function(X)
        result["rul"] = rul_model.predict(X)
        return result

    #add trend(current-mean) or z-score + summarize in sensor importance not only engine domain 

# ============================================================
    # OUR ADDITION 6: Replace the old dataframe + text display
    # with KPI bar, fleet charts, and engine grid
    # ============================================================
    with placeholder.container():

        # ---------- KPI Bar (3 cards) ----------
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Engines", len(df))
        with col2:
            st.metric("Anomaly Engines", int((df["status"] == "Anomaly").sum()))
        with col3:
            st.metric("Normal Engines", int((df["status"] == "Normal").sum()))

        # ---------- Fleet Analytics Charts ----------
        st.divider()
        st.subheader("Fleet Analytics")
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            # Group anomaly scores into buckets and count them
            bins = [-float("inf"), -0.5, 0, 0.5, float("inf")]
            labels = ["Very Low", "Low", "Medium", "High"]
            df["score_bucket"] = pd.cut(df["anomaly_score"], bins=bins, labels=labels)
            bucket_counts = df["score_bucket"].value_counts().sort_index()
            st.bar_chart(bucket_counts, use_container_width=True)
            st.caption("Anomaly Score Distribution")
        with chart_col2:
            # Count how many anomaly events each engine has
            anomaly_counts = df[df["status"] == "Anomaly"]["engine_id"].value_counts()
            if not anomaly_counts.empty:
                st.bar_chart(anomaly_counts, use_container_width=True)
                st.caption("Anomaly Count per Engine")
            else:
                st.info("No anomalies to display")

        # ---------- Engine Card Grid (10 columns) ----------
        st.divider()
        st.subheader("Fleet Overview")
        engines = df["engine_id"].unique()
        cols = st.columns(10)

        for i, eng in enumerate(engines):
            engine_data = df[df["engine_id"] == eng]
            latest = engine_data.iloc[-1]       # latest cycle for this engine
            status = latest["status"]
            icon = "🔴" if status == "Anomaly" else "🟢"

            with cols[i % 10]:                   # distribute across 10 columns, wrap to next row
                if st.button(f"{icon} {eng} - {status}",
                             key=f"eng_{eng}",
                             use_container_width=True):
                    show_engine_detail(latest)   # open the pop‑up with this engine's data

    st_autorefresh(interval=15000, key="datarefresh")