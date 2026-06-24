from db.db_client import fetch_latest_cycle_per_engine, fetch_all_cycles
from collections import defaultdict, deque
from config import SENSORS, ROLLING_WINDOW_SIZE
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import numpy as np
import streamlit as st
from ui.utils.event_builder import EngineState
import json
import joblib


st.set_page_config(page_title="Predictive Maintenance", layout="wide")
st.title("Live Anomaly Monitoring")
placeholder = st.empty()

def safe_parse(x):
    if isinstance(x, dict):
        return x
    if isinstance(x, str):
        return json.loads(x)
    raise ValueError(f"Unsupported type: {type(x)}")

df = fetch_latest_cycle_per_engine()

if df.empty:
    with placeholder.container():
        st.warning("No data in database yet")
        st_autorefresh(interval=5000, key="dfrefresh")

else:
    st.dataframe(df)