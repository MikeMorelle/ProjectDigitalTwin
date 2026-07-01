from db.db_client import fetch_latest_cycle_per_engine, fetch_engine_history
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import numpy as np
import streamlit as st
import requests

st.set_page_config(page_title="Predictive Maintenance", layout="wide")
st.title("Live Anomaly Monitoring")
placeholder = st.empty()

# =========================
# SESSION STATE – things the app remembers between refreshes
# =========================
if "run_id" not in st.session_state:
    try:
        status = requests.get("http://api:8000/status").json()
        st.session_state.run_id = status.get("run_id")
    except:
        st.write("Start run first!")

# shutdown_engines – list of engine IDs that are currently shut down
if "shutdown_engines" not in st.session_state:
    st.session_state.shutdown_engines = []

# confirm_shutdown_engine – engine waiting for confirmation (two‑step)
if "confirm_shutdown_engine" not in st.session_state:
    st.session_state.confirm_shutdown_engine = None

# refresh_paused – is the auto‑refresh paused?
if "refresh_paused" not in st.session_state:
    st.session_state.refresh_paused = False

# refresh_interval_sec – how many seconds between auto‑refreshes
if "refresh_interval_sec" not in st.session_state:
    st.session_state.refresh_interval_sec = 15

# SHAP cache – stores top‑factor results per engine to avoid repeated API calls
if "shap_cache" not in st.session_state:
    st.session_state.shap_cache = {}

# =========================
# HELPER FUNCTIONS
# =========================
def get_api_interval():
    """Ask the API what interval the producer is streaming at."""
    try:
        resp = requests.get("http://api:8000/status", timeout=2)
        data = resp.json()
        return data.get("interval", 15)
    except:
        return 15

def fetch_shap_top_factors(engine_id):
    """Return the top 3 SHAP‑important sensor names for one engine."""
    # First, get the current dataset name from the API
    dataset_num = ""
    try:
        status = requests.get("http://api:8000/status", timeout=2).json()
        dataset_num = status.get("dataset", "")
    except:
        pass

    try:
        resp = requests.post(
            "http://api:8000/explain/shap",
            params={
                "run_id": st.session_state.run_id,
                "engine_id": engine_id,
                "dataset_num": dataset_num
            },
            timeout=30
        )
        data = resp.json()
        contributions = data.get("feature_contributions", [])
        # Sort by absolute importance, take the top 3 features
        sorted_contribs = sorted(contributions, key=lambda x: abs(x["value"]), reverse=True)
        return [item["feature"] for item in sorted_contribs[:3]]
    except:
        pass
    return []

# =========================
# SIDEBAR – settings and filters
# =========================
with st.sidebar:
    st.header("⚙️ Dashboard Settings")

    api_interval = get_api_interval()
    st.caption(f"Setup Interval every {api_interval}s")
    st.caption(f"Dashboard refreshes every {st.session_state.refresh_interval_sec}s")

    st.session_state.refresh_paused = st.checkbox(
        "Pause auto‑refresh",
        value=st.session_state.refresh_paused
    )

    options = sorted(set([5, 10, 15, 30, 60, api_interval]))
    current = st.session_state.refresh_interval_sec
    if current not in options:
        current = api_interval
    st.session_state.refresh_interval_sec = st.selectbox(
        "Refresh interval (seconds)",
        options=options,
        index=options.index(current)
    )

    st.divider()
    st.subheader("🔍 Engine Filter")
    search_text = st.text_input(
        "Search engine ID (exact)",
        value="",
        placeholder="e.g. 5",
        key="sidebar_search"
    )
    show_shutdown = st.checkbox(
        "Show only shutdown engines",
        value=False,
        key="sidebar_show_shutdown"
    )

# =========================
# REACTIVATION POPUP (for a shutdown engine)
# =========================
@st.dialog("Engine Detail", width="large")
def show_shutdown_engine_detail(engine_data):
    eng = engine_data["engine_id"]
    st.header(f"Engine {eng} – Shutdown")
    st.info("This engine has been shut down and is not being monitored.")

    if st.button(f"🔄 Reactivate Engine {eng}", key=f"reactivate_{eng}"):
        st.session_state.shutdown_engines.remove(eng)
        st.success(f"Engine {eng} has been reactivated!")
        st.rerun()

# =========================
# ENGINE DETAIL POPUP (full information for one active engine)
# =========================
@st.dialog("Engine Detail", width="large")
def show_engine_detail(engine_data):
    eng = engine_data["engine_id"]

    # ---- Two‑step shutdown confirmation ----
    if st.session_state.confirm_shutdown_engine == eng:
        st.warning(f"Are you sure you want to shut down Engine {eng}?")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Yes, confirm", key=f"confirm_yes_{eng}"):
                st.session_state.shutdown_engines.append(eng)
                st.session_state.confirm_shutdown_engine = None
                st.success(f"Engine {eng} has been shut down.")
                st.rerun()
        with col_no:
            if st.button("Cancel", key=f"confirm_no_{eng}"):
                st.session_state.confirm_shutdown_engine = None
                st.rerun()
        return

    st.header(f"Engine {eng} Detail Report")

    # ---- Four KPI cards ----
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Cycle", engine_data["cycle"])
    with col2:
        st.metric("Anomaly Score", f"{engine_data['anomaly_score']:.2f}")
    with col3:
        rul_value = engine_data["rul"]
        st.metric("Estimated RUL", "N/A" if pd.isna(rul_value) else f"{rul_value:.0f} cycles")
    with col4:
        true_rul_value = engine_data.get("true_rul")
        st.metric("Real RUL", "N/A" if pd.isna(true_rul_value) else f"{true_rul_value:.0f} cycles")

    # ---- Maintenance recommendation ----
    st.subheader("Maintenance Recommendation")
    score = engine_data["anomaly_score"]
    if score < -1.0:
        st.error("🔴 Critical — Immediate inspection recommended.")
    elif score < 0:
        st.warning("🟡 Warning — Schedule maintenance within next cycles.")
    else:
        st.success("🟢 Normal — Engine operating normally.")

    # ---- Top Contributing Factors (SHAP) ----
    top_factors = engine_data.get("top_factors", [])
    history = fetch_engine_history(eng, st.session_state.run_id)

    if not top_factors and not history.empty:
        # Try cache first, then API (with a spinner while loading)
        if eng in st.session_state.shap_cache:
            top_factors = st.session_state.shap_cache[eng]
        else:
            with st.spinner("Loading SHAP explanation…"):
                top_factors = fetch_shap_top_factors(eng)
                st.session_state.shap_cache[eng] = top_factors

    if top_factors:
        st.subheader("Top Contributing Factors")
        for i, f in enumerate(top_factors, 1):
            st.write(f"{i}. {f}")

    # ---- Historical Trends (anomaly score and RUL) ----
    if not history.empty:
        st.subheader("Trends Over Time")
        st.line_chart(history.set_index("cycle")["anomaly_score"])
        st.caption("Anomaly Score per Cycle")

        # RUL comparison chart (predicted vs true)
        if "true_rul" in history.columns:
            st.subheader("Predicted vs True Remaining Useful Life")
            compare = history.set_index("cycle")[["rul", "true_rul"]]
            compare.columns = ["Predicted RUL", "True RUL"]
            st.line_chart(compare)
            st.caption("Predicted vs True Remaining Useful Life")

    # ---------- Sensor Trends (raw sensor values) ----------
    st.subheader("Sensor Trends (Live Stream)")
    if not history.empty:
        sensors_expanded = history["sensors"].apply(pd.Series)
        sensors_expanded["cycle"] = history["cycle"]
        sensors_expanded = sensors_expanded.set_index("cycle")

        all_sensors = sorted(sensors_expanded.columns.tolist())

        # Default selection: the 3 most drifted sensors (or first 3 if not enough data)
        if len(history) >= 10:
            baseline_mean = sensors_expanded.iloc[:10].mean()
            latest = sensors_expanded.iloc[-1]
            drift = (latest - baseline_mean).abs().sort_values(ascending=False)
            default_sensors = drift.index[:3].tolist()
        else:
            default_sensors = all_sensors[:3]

        selected = st.multiselect(
            "Select sensors to display",
            all_sensors,
            default=default_sensors,
            key=f"sensors_{eng}"
        )
        if selected:
            st.line_chart(sensors_expanded[selected], use_container_width=True)
    else:
        st.info("No sensor data yet for this engine.")

    # ============================================================
    # Baseline Deviation – how far has each sensor drifted?
    # ============================================================
    st.divider()
    st.subheader("Baseline Deviation")

    if history.empty or len(history) < 10:
        st.info("Need at least 10 cycles to compute baseline.")
    else:
        # Build a table from the sensor JSON
        sensor_table = history["sensors"].apply(pd.Series)
        sensor_table["cycle"] = history["cycle"]
        sensor_table = sensor_table.set_index("cycle")

        # Healthy baseline = first 10 cycles
        first_10 = sensor_table.index[:10]
        healthy_mean = sensor_table.loc[first_10].mean()
        healthy_std  = sensor_table.loc[first_10].std()

        # Avoid division by zero
        for col in healthy_std.index:
            if healthy_std[col] == 0:
                healthy_std[col] = 1.0

        # Choose display mode
        mode = st.radio(
            "Display mode",
            options=["Deviation (Current – Mean)", "Z‑Score"],
            horizontal=True,
            key=f"deviation_mode_{eng}"
        )

        # Calculate the values for the chosen mode
        if mode == "Z‑Score":
            values_df = (sensor_table - healthy_mean) / healthy_std
            chart_caption = "Z‑Score = (current – healthy mean) / healthy std"
            chart_warning = "│Z│ > 2 → unusual, │Z│ > 3 → critical"
        else:
            values_df = sensor_table - healthy_mean
            chart_caption = "Deviation = current value – healthy mean"
            chart_warning = "Large deviation → sensor has drifted from its normal level"

        # ---- KPI cards for the 3 most drifted sensors ----
        latest_values = values_df.iloc[-1]
        drift = latest_values.abs().sort_values(ascending=False)
        kpi_sensors = drift.index[:3].tolist()

        if kpi_sensors:
            st.caption(f"Current {'z‑score' if mode == 'Z‑Score' else 'deviation'} of top drifted sensors")
            kpi_cols = st.columns(len(kpi_sensors))
            for idx, sensor_name in enumerate(kpi_sensors):
                current_val = latest_values[sensor_name]

                # Choose colour based on severity
                if mode == "Z‑Score":
                    if abs(current_val) >= 3:
                        icon = "🔴"
                    elif abs(current_val) >= 1.5:
                        icon = "🟡"
                    else:
                        icon = "🟢"
                else:
                    s_std = healthy_std[sensor_name]
                    if abs(current_val) >= 3 * s_std:
                        icon = "🔴"
                    elif abs(current_val) >= 1.5 * s_std:
                        icon = "🟡"
                    else:
                        icon = "🟢"
                with kpi_cols[idx]:
                    st.metric(label=sensor_name, value=f"{icon} {current_val:.2f}")

        # ---- Trend chart ----
        default_dev = kpi_sensors if kpi_sensors else sorted(values_df.columns.tolist())[:3]
        selected_dev = st.multiselect(
            f"Select sensors ({'z‑score' if mode == 'Z‑Score' else 'deviation'})",
            sorted(values_df.columns.tolist()),
            default=default_dev,
            key=f"dev_sensors_{eng}_{mode}"
        )
        if selected_dev:
            st.line_chart(values_df[selected_dev], use_container_width=True)
            st.caption(chart_caption)
            st.caption(chart_warning)

    # ---- Shutdown button (only when not already confirming) ----
    if st.session_state.confirm_shutdown_engine != eng:
        st.divider()
        if st.button(f"🛑 Shutdown Engine {eng}", key=f"shutdown_trigger_{eng}"):
            st.session_state.confirm_shutdown_engine = eng

# =========================
# MAIN PAGE
# =========================
df = fetch_latest_cycle_per_engine(st.session_state.run_id)

if df.empty:
    with placeholder.container():
        st.warning("No data in database yet")
        st_autorefresh(interval=5000, key="dfrefresh")

else:
    df["status"] = df["anomaly_score"].apply(lambda x: "Anomaly" if x < 0 else "Normal")

    with placeholder.container():

        # KPI Bar
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Engines", len(df))
        with col2:
            st.metric("Anomaly Engines", int((df["status"] == "Anomaly").sum()))
        with col3:
            st.metric("Normal Engines", int((df["status"] == "Normal").sum()))

        st.divider()

        # Engine Grid
        st.subheader("Fleet Overview")
        engines = df["engine_id"].unique()
        cols = st.columns(10)

        for i, eng in enumerate(engines):
            latest = df[df["engine_id"] == eng].iloc[-1]
            is_shutdown = eng in st.session_state.shutdown_engines

            # Apply filters (show shutdown / search)
            if show_shutdown and not is_shutdown:
                continue
            if search_text.strip() != "" and str(eng).strip().lower() != search_text.strip().lower():
                continue

            with cols[i % 10]:
                if is_shutdown:
                    if st.button(f"⚫ Engine: {eng} - Shutdown", key=f"eng_{eng}", width='stretch'):
                        show_shutdown_engine_detail(latest)
                else:
                    icon = "🔴" if latest["status"] == "Anomaly" else "🟢"
                    if st.button(f"{icon} Engine: {eng} - {latest['status']}", key=f"eng_{eng}", width='stretch'):
                        show_engine_detail(latest)

    # Auto‑refresh
    if st.session_state.refresh_paused:
        refresh_ms = int(1e9)  # huge number = practically paused
    else:
        refresh_ms = st.session_state.refresh_interval_sec * 1000

    st_autorefresh(interval=refresh_ms, key="datarefresh")