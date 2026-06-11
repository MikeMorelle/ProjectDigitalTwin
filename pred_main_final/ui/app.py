import streamlit as st
from db.db_client import fetch_latest_cycle_per_engine
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Predictive Maintenance", layout="wide")
st.title("Live Anomaly Monitoring")
placeholder = st.empty()

#states
if "shutdown_engines" not in st.session_state:
    st.session_state.shutdown_engines = []

if "selected_engine" not in st.session_state:
    st.session_state.selected_engine = None

def get_status(score):
    if score < 0:
        return "Anomaly"
    else:
        return "Normal"

df = fetch_latest_cycle_per_engine()

if df.empty:
    with placeholder.container():
        st.warning("No data in database yet")
        st_autorefresh(interval=5000, key="dfrefresh")

df["status"] = df["anomaly_score"].apply(get_status)

# filter shutdown engines, later in db to optimize
df = df[~df["engine_id"].isin(st.session_state.shutdown_engines)]

#Overview
with placeholder.container():
    st.metric("Events", len(df))
    st.metric("Warning", int((df["status"] == "Anomaly").sum()))
    st.dataframe(df.tail(20))

    #engine list
    st.subheader("Engines")
    engines = df["engine_id"].unique()

    for i,eng in enumerate(engines):
        engine_data = df[df["engine_id"] == eng]
        latest = engine_data.iloc[-1]
        status = latest["status"]
        color = "🔴" if status == "Anomaly" else "🟢"

        #popup
        with st.popover(f"{color} Engine {eng}"):
            st.write("Engine Details")
            st.write(f"Anomaly Score: {latest['anomaly_score']:.2f}")
            st.write(f"Status: {status}")
            st.write(f"Cycle: {latest['cycle']}")

            #shutdown button
            if st.button(f"Shutdown Engine {eng}", key=f"shutdown_{eng}"):
                st.session_state.shutdown_engines.append(eng)
                st.success(f"Engine {eng} shutdown initiated!")
                st.rerun()
                    
            #close
            if st.button("Close", key=f"close_{eng}"):
                st.rerun()

st_autorefresh(interval=15000, key="datarefresh")
