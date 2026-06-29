from ui.utils.turbofan import compute_streaks, render_engine
import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
from db.db_client import fetch_engine_history

#ab wie vielen Zyklen ein Sensor als unverändert gilt
STREAK_THRESHOLD = 5

if "run_id" not in st.session_state:

    try:
        api_status = requests.get("http://api:8000/status").json()
        st.session_state.run_id = api_status["run_id"]

    except Exception:
        st.error("API not ready.")
        st.stop()

else:
    st.stop()

data = fetch_engine_history(
    engine_id=3,
    run_id=st.session_state.run_id
)

sensor_df = pd.json_normalize(data["sensors"])
sensor_df["cycle"] = data["cycle"]

sensor_df = sensor_df.sort_values("cycle")

streak_df = sensor_df.copy()

for col in sensor_df.columns:

    if col != "cycle":
        streak_df[f"{col}_streak"] = compute_streaks(sensor_df[col])

latest = streak_df.iloc[-1]

render_engine(latest)
