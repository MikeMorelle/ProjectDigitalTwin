from db.db_client import fetch_latest_cycle_per_engine, fetch_engine_history # fetch_engine_history  – to get all cycles of one engine for trend charts
from streamlit_autorefresh import st_autorefresh
import joblib
import pandas as pd
#import shap
import numpy as np
import streamlit as st
import requests

def get_run_id():
    try: 
        response = requests.get("http://api:8000/status")
        return response.json()
    except:
        return {"running": False}

# =========================
# SESSION STATE
# =========================
if "run_id" not in st.session_state:
    try:
        status = requests.get("http://api:8000/status").json()
        st.session_state.run_id = status.get("run_id")
    except:
        st.write("Start run first!")

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

# ---- Auto‑refresh state ----
if "refresh_paused" not in st.session_state:
    st.session_state.refresh_paused = False          # is the refresh paused?

if "refresh_interval_sec" not in st.session_state:
    st.session_state.refresh_interval_sec = 15       # default: refresh every 15 seconds

# ---- Check shutdown state ----
if "confirm_shutdown_engine" not in st.session_state:
    st.session_state.confirm_shutdown_engine = None

# ============================================================
# Helper: ask the API what interval the producer is using
# ============================================================
def get_api_interval():
    """
    Ask the Setup page's API what streaming interval is active.
    If the API is unreachable, return 15 as a safe default.
    """
    try:
        response = requests.get("http://api:8000/status", timeout=2)
        data = response.json()
        return data.get("interval", 15)
    except:
        return 15
    
# ============================================================
# Sidebar – Auto‑refresh controls
# ============================================================
with st.sidebar:
    st.header("⚙️ Dashboard Settings")

    # 1. Ask the API what interval the producer is streaming at
    api_interval = get_api_interval()

    # Show the API streaming interval (auto‑updates from Setup page)
    st.caption(f"Setup Interval every {api_interval}s")
    # Show the current dashboard refresh interval (changes instantly)
    st.caption(f"Dashboard refreshes every {st.session_state.refresh_interval_sec}s")

    # 2. Pause / resume checkbox
    st.session_state.refresh_paused = st.checkbox(
        "Pause auto‑refresh",
        value=st.session_state.refresh_paused
    )

    # 3. Refresh interval dropdown
    # Include the API interval in the options so it auto‑matches
    options = sorted(set([5, 10, 15, 30, 60, api_interval]))

    # Make sure the current value is in the list
    current = st.session_state.refresh_interval_sec
    if current not in options:
        current = api_interval

    st.session_state.refresh_interval_sec = st.selectbox(
        "Refresh interval (seconds)",
        options=options,
        index=options.index(current)
    )

    # ---- Engine search & filter ----
    st.divider()
    st.subheader("🔍 Engine Filter")

    # Text box – the engineer types part of an engine ID
    search_text = st.text_input(
        "Search engine ID",
        value="",
        placeholder="e.g. 5 or ENG‑01",
        key="sidebar_search"
    )

    # Checkbox – show/hide shutdown engines
    show_shutdown = st.checkbox(
        "Show shutdown engines",
        value=False,                          # by default hide them
        key="sidebar_show_shutdown"
    )

# ============================================================
# simple pop‑up for engine reactivation
# ============================================================
@st.dialog("Engine Detail", width="large")
def show_shutdown_engine_detail(engine_data):
    """
    Show a simple pop‑up for a shutdown engine.
    The engineer can reactivate it here.
    """
    eng = engine_data["engine_id"]
    st.header(f"Engine {eng} – Shutdown")
    st.info("This engine has been shut down and is not being monitored.")

    if st.button(f"🔄 Reactivate Engine {eng}", key=f"reactivate_{eng}"):
        st.session_state.shutdown_engines.remove(eng)
        st.success(f"Engine {eng} has been reactivated!")
        st.rerun()

# ============================================================
# ADDITION 1: Dialog – shown when an engine card is clicked (POP UP)
# ============================================================

@st.dialog("Engine Detail", width="large")
def show_engine_detail(engine_data):
    """
    Show full details for one engine.
    engine_data is one row from our main DataFrame,
    which already has anomaly_score, rul, status, and top_factors.
    """
    eng = engine_data["engine_id"]

    # ---------- Shutdown confirmation (if the user just clicked "Shutdown") ----------
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

    # ---- Basic info ----
    st.header(f"Engine {eng} Detail Report")

    # ---- Three KPI cards ----
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Cycle", engine_data["cycle"])
    with col2:
        st.metric("Anomaly Score", f"{engine_data['anomaly_score']:.2f}")
    with col3:
        rul_value = engine_data["rul"]

        if not np.isnan(rul_value):
                        st.metric("Estimated Remaining Useful Life (RUL)", f"{rul_value:.0f} cycles")
        else:
            st.metric("Remaining Useful Life (RUL)", "N/A")
    with col4:
        true_rul = engine_data["true_rul"]
        if not np.isnan(rul_value):
                        st.metric("Real Remaining Useful Life (RUL)", f"{true_rul:.0f} cycles")
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
    history = fetch_engine_history(eng, st.session_state.run_id)        # get all cycles from the database
    if not history.empty:
        # compute_predictions is defined later in the main block,
        # because it needs the loaded models. We'll call it now.
        #history = compute_predictions(history)  # add anomaly_score & rul columns
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.line_chart(history.set_index("cycle")["anomaly_score"], width='stretch')
            st.caption("Anomaly Score per Cycle")
        with chart_col2:
            st.line_chart(history.set_index("cycle")["rul"], width='stretch')
            st.caption("RUL per Cycle (higher = more life left)")

    # ---------- Sensor Trends (Live from DB) ----------
    st.subheader("Sensor Trends (Live Stream)")
    # history was already fetched above
    if not history.empty:
        # Expand the JSON 'sensors' column into real columns
        sensors_expanded = history["sensors"].apply(pd.Series)
        sensors_expanded["cycle"] = history["cycle"]
        sensors_expanded = sensors_expanded.set_index("cycle")

        all_sensors = sorted([s for s in sensors_expanded.columns])
        # Default: first 3 roll_mean sensors (clean, intuitive start)
        default_sensors = all_sensors[:3]

        selected = st.multiselect(
            "Select sensors to display",
            all_sensors,
            default=default_sensors,
            key=f"sensors_{eng}"
        )
        if selected:
            st.line_chart(sensors_expanded[selected], width='stretch')
    else:
        st.info("No sensor data yet for this engine.")

    # ============================================================
    # Baseline Deviation – how far has each sensor drifted?
    # ============================================================
    st.divider()
    st.subheader("Baseline Deviation")

    # We can only do this if we have enough history and SHAP info
    if history.empty or len(history) < 10:
        st.info("Need at least 10 cycles to compute baseline.")
 
    else:
        # ---------- 1. Build a table from the sensor JSON ----------
        # Each row = one cycle, each column = one sensor (e.g. sensor_2_roll_mean)
        sensor_table = history["sensors"].apply(pd.Series)
        sensor_table["cycle"] = history["cycle"]
        sensor_table = sensor_table.set_index("cycle")

        # ---------- 2. Calculate the healthy baseline ----------
        # We use the first 10 cycles as "healthy"
        first_10 = sensor_table.index[:10]                    # cycle numbers 1–10
        healthy_mean = sensor_table.loc[first_10].mean()      # average for each sensor
        healthy_std  = sensor_table.loc[first_10].std()       # normal variation for each sensor

        # If a sensor never changed at all, set its std to 1 (avoids division by zero)
        for col in healthy_std.index:
            if healthy_std[col] == 0:
                healthy_std[col] = 1.0

        # ---------- 3. Let the user choose the mode ----------
        mode = st.radio(
            "Display mode",
            options=["Deviation (Current – Mean)", "Z‑Score"],
            horizontal=True,
            key=f"deviation_mode_{eng}"
        )

        # ---------- 4. Calculate the values for the chosen mode ----------
        if mode == "Z‑Score":
            # Z‑Score = (value – healthy_mean) / healthy_std
            values_df = (sensor_table - healthy_mean) / healthy_std
            chart_caption = "Z‑Score = (current – healthy mean) / healthy std"
            chart_warning = "│Z│ > 2 → unusual, │Z│ > 3 → critical"
        else:
            # Deviation = value – healthy_mean
            values_df = sensor_table - healthy_mean
            chart_caption = "Deviation = current value – healthy mean"
            chart_warning = "Large deviation → sensor has drifted from its normal level"

        # ---------- 5. KPI cards for the top 3 SHAP sensors ----------
        # Get the latest cycle's values
        latest_values = values_df.iloc[-1]

        # Pick up to 3 SHAP sensors that actually exist in our table
        kpi_sensors = []
        for sensor in history["sensors"].keys():
            if sensor in latest_values.index:
                kpi_sensors.append(sensor)
        kpi_sensors = kpi_sensors[:3]   # only the first 3

        if len(kpi_sensors) > 0:
            st.caption(f"Current {'z‑score' if mode == 'Z‑Score' else 'deviation'} of top contributing sensors")

            # Create one column per sensor
            kpi_cols = st.columns(len(kpi_sensors))

            for idx, sensor_name in enumerate(kpi_sensors):
                current_val = latest_values[sensor_name]

                # Decide the colour based on how far the value is from zero
                if mode == "Z‑Score":
                    # For z‑score, 1.5 = warning, 3 = critical
                    if abs(current_val) >= 3:
                        icon = "🔴"
                    elif abs(current_val) >= 1.5:
                        icon = "🟡"
                    else:
                        icon = "🟢"
                else:
                    # For deviation, compare to 1.5× and 3× the sensor's own healthy std
                    sensor_std = healthy_std[sensor_name]
                    if abs(current_val) >= 3 * sensor_std:
                        icon = "🔴"
                    elif abs(current_val) >= 1.5 * sensor_std:
                        icon = "🟡"
                    else:
                        icon = "🟢"

                with kpi_cols[idx]:
                    st.metric(label=sensor_name, value=f"{icon} {current_val:.2f}")

        # ---------- 6. Trend chart ----------
        # Default selection = the same KPI sensors, or first 3 sensors if none
        default_sensors = kpi_sensors if len(kpi_sensors) > 0 else sorted(values_df.columns.tolist())[:3]

        selected = st.multiselect(
            f"Select sensors ({'z‑score' if mode == 'Z‑Score' else 'deviation'})",
            sorted(values_df.columns.tolist()),
            default=default_sensors,
            key=f"dev_sensors_{eng}"
        )

        if selected:
            st.line_chart(values_df[selected], width='stretch')
            st.caption(chart_caption)
            st.caption(chart_warning)

    # ---- Shutdown button (only show if NOT already confirming) ----
    if st.session_state.confirm_shutdown_engine != eng:
        st.divider()
        if st.button(f"🛑 Shutdown Engine {eng}", key=f"shutdown_trigger_{eng}"):
            st.session_state.confirm_shutdown_engine = eng

df = fetch_latest_cycle_per_engine(st.session_state.run_id)

if df.empty:
    with placeholder.container():
        st.warning("No data in database yet")
        st_autorefresh(interval=5000, key="dfrefresh")

else:
    # rul_bundle = joblib.load("ml/models/latest/rul_model.joblib")
    # rul_model = rul_bundle["rul_model"]

    # ano_bundle = joblib.load("ml/models/latest/ano_model.joblib")
    # ano_model = ano_bundle["model"]
    # #explainer = shap.TreeExplainer(ano_model)

    # ops_df = df["ops"].apply(pd.Series)
    # sensors_df = df["sensors"].apply(pd.Series)
    # X = pd.concat([ops_df, sensors_df], axis=1)

    # X = X.reindex(columns=rul_model.feature_names_in_)

    # X = X.astype(float)

    # df["rul"] = rul_model.predict(X)
    # df["anomaly_score"] = ano_model.decision_function(X)
    # df["top_factors"] = None
    # anomaly_idx = df[df["anomaly_score"] < 0].index
    # for i in anomaly_idx:
    #     sample = X.loc[[i]]
    #     shap_values = explainer.shap_values(sample)
    #     importance = pd.Series(np.abs(shap_values[0]), index=X.columns).sort_values(ascending=False)
    #     top3 = importance.head(3)
    #     df.at[i, "top_factors"] = list(top3.index)
    
    # ============================================================
    # ADDITION 2: compute status from anomaly score
    # (instead of the old get_status function which used is_anomaly)
    # ============================================================
    df["status"] = df["anomaly_score"].apply(lambda x: "Anomaly" if x < 0 else "Normal")

    # ============================================================
    # ADDITION 3: define compute_predictions HERE inside Engine detail (POP UP),
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
    # ADDITION 4: Replace the old dataframe + text display
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
        
        # st.divider()
        # st.subheader("Fleet Analytics")
        # chart_col1, chart_col2 = st.columns(2)
        # with chart_col1:
        #     # Group anomaly scores into buckets and count them
        #     bins = [-float("inf"), -0.5, 0, 0.5, float("inf")]
        #     labels = ["Very Low", "Low", "Medium", "High"]
        #     df["score_bucket"] = pd.cut(df["anomaly_score"], bins=bins, labels=labels)
        #     bucket_counts = df["score_bucket"].value_counts().sort_index()
        #     st.bar_chart(bucket_counts, use_container_width=True)
        #     st.caption("Anomaly Score Distribution")
        # with chart_col2:
        #     # Count how many anomaly events each engine has
        #     anomaly_counts = df[df["status"] == "Anomaly"]["engine_id"].value_counts()
        #     if not anomaly_counts.empty:
        #         st.bar_chart(anomaly_counts, use_container_width=True)
        #         st.caption("Anomaly Count per Engine")
        #     else:
        #         st.info("No anomalies to display")
        
        # ---------- Engine Card Grid (10 columns) ----------
        st.divider()
        st.subheader("Fleet Overview")
        engines = df["engine_id"].unique()
        cols = st.columns(10)

        for i, eng in enumerate(engines):
            engine_data = df[df["engine_id"] == eng]
            latest = engine_data.iloc[-1]       # latest cycle for this engine
            status = latest["status"]
            
            # Check if this engine has been shut down
            is_shutdown = eng in st.session_state.shutdown_engines

            # ---- Filter 1: if checkbox is ticked, show ONLY shutdown engines ----
            if show_shutdown:
                if not is_shutdown:
                    continue
            # If checkbox is NOT ticked, show ALL engines (active + shutdown)

            # ---- Filter 2: exact ID search ----
            if search_text.strip() != "":
                # Compare as strings, but trim and ignore case
                if str(eng).strip().lower() != search_text.strip().lower():
                    continue

            with cols[i % 10]:
                if is_shutdown:
                    # Shutdown engine – grey, but still clickable
                    icon = "⚫"
                    label = f"{icon} {eng} - Shutdown"
                    if st.button(label, key=f"eng_{eng}", width='stretch'):
                        show_shutdown_engine_detail(latest)
                else:
                    # Active engine – coloured icon
                    icon = "🔴" if status == "Anomaly" else "🟢"
                    label = f"{icon} {eng} - {status}"
                    if st.button(label, key=f"eng_{eng}", width='stretch'):
                        show_engine_detail(latest)  # open the pop‑up with this engine's data

    # ---- Auto‑refresh – pause or use chosen interval ----
    if st.session_state.refresh_paused:
        # A huge number means "never refresh" (well, once every ~11 days)
        refresh_ms = int(1e9)
    else:
        # Convert seconds to milliseconds
        refresh_ms = st.session_state.refresh_interval_sec * 1000

    st_autorefresh(interval=refresh_ms, key="datarefresh")