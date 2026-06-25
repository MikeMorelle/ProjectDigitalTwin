from db.db_client import fetch_latest_cycle_per_engine, fetch_engine_history
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import numpy as np
import streamlit as st

st.set_page_config(page_title="Predictive Maintenance", layout="wide")
st.title("Live Anomaly Monitoring")

placeholder = st.empty()

# =========================
# SESSION STATE
# =========================
if "selected_engine" not in st.session_state:
    st.session_state.selected_engine = None


def get_status(is_anomaly: bool):
    return "Anomaly" if is_anomaly else "Normal"


# =========================
# ENGINE DETAIL POPUP
# =========================
@st.dialog("Engine Detail", width="large")
def show_engine_detail(engine_data):
    eng = engine_data["engine_id"]

    st.header(f"Engine {eng} Detail Report")

    # KPI
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Cycle", engine_data["cycle"])
    with col2:
        st.metric("Anomaly Score", f"{engine_data['anomaly_score']:.2f}")
    with col3:
        rul_value = engine_data["rul"]
        st.metric("RUL (cycles)", "N/A" if pd.isna(rul_value) else f"{rul_value:.0f}")

    # Status
    st.subheader("Maintenance Recommendation")
    score = engine_data["anomaly_score"]

    if score < -1:
        st.error("🔴 Critical — Immediate inspection required.")
    elif score < 0:
        st.warning("🟡 Warning — Schedule maintenance soon.")
    else:
        st.success("🟢 Normal operation.")

    # Top factors (from backend)
    top_factors = engine_data.get("top_factors", [])
    if top_factors:
        st.subheader("Top Contributing Factors")
        for i, f in enumerate(top_factors, 1):
            st.write(f"{i}. {f}")

    # =========================
    # HISTORY CHARTS
    # =========================
    st.subheader("Trends Over Time")

    history = fetch_engine_history(eng)

    if not history.empty:
        st.line_chart(history.set_index("cycle")["anomaly_score"])
        st.caption("Anomaly Score per Cycle")

        st.line_chart(history.set_index("cycle")["rul"])
        st.caption("RUL per Cycle")

        # SENSOR TRENDS
        st.subheader("Sensor Trends")

        sensors = history["sensors"].apply(pd.Series)
        sensors["cycle"] = history["cycle"]
        sensors = sensors.set_index("cycle")

        selected = st.multiselect(
            "Select sensors",
            sensors.columns,
            default=list(sensors.columns[:3]),
            key=f"sensors_{eng}"
        )

        if selected:
            st.line_chart(sensors[selected])
    else:
        st.info("No history data available.")


# =========================
# MAIN DATA
# =========================
df = fetch_latest_cycle_per_engine()

if df.empty:
    with placeholder.container():
        st.warning("No data in database yet")
        st_autorefresh(interval=5000, key="refresh_empty")

else:
    # status derived from backend flag
    df["status"] = df["is_anomaly"].map({True: "Anomaly", False: "Normal"})

    with placeholder.container():

        # =========================
        # KPI BAR
        # =========================
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Engines", len(df))

        with col2:
            st.metric("Anomalies", int(df["is_anomaly"].sum()))

        with col3:
            st.metric("Normal", int((~df["is_anomaly"]).sum()))

        st.divider()

        # =========================
        # ENGINE GRID
        # =========================
        st.subheader("Fleet Overview")

        engines = df["engine_id"].unique()
        cols = st.columns(10)

        for i, eng in enumerate(engines):
            latest = df[df["engine_id"] == eng].iloc[-1]

            icon = "🔴" if latest["is_anomaly"] else "🟢"

            with cols[i % 10]:
                if st.button(
                    f"{icon} {eng}",
                    key=f"eng_{eng}",
                    use_container_width=True
                ):
                    show_engine_detail(latest)

    st_autorefresh(interval=15000, key="refresh_main")