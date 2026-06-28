import streamlit as st
import requests
from config import fault_config

st.title("Kafka Control")

def get_status():
    try: 
        response = requests.get("http://api:8000/status")
        return response.json()
    except:
        return {"running": False}

status = get_status()
running = status.get("running", False)
st.write(f"Producer status: {'🟢 running' if running else '🔴 stopped'}")

dataset = st.selectbox(
    "Which dataset do you want to use?",
    ["FD001","FD002","FD003","FD004",]
)

interval = st.selectbox(
    "In which time interval (s) do you want the data to be streamed?",
    [5, 10, 15,60,90]
)

bias = st.selectbox(
    "Which fault scenario do you want to implement?",
    list(fault_config.keys())
)

#which models + edge/frontend ML calc

if st.button("Start Streaming!"):
    with st.spinner("Starting producer..."):
        response = requests.post(
            "http://api:8000/start",
            json = {
                "dataset": dataset,
                "interval": interval,
                "fault_config": fault_config[bias]
        }
    )
    res = response.json()
    st.session_state.run_id = res["run_id"]
    st.json(response.json())
    st.success(f"Start sensor data streaming with {dataset} every {interval} seconds. With id: {st.session_state.run_id} ")

if st.button("Reset Streaming"):
    with st.spinner("Resetting..."):
        response = requests.post("http://api:8000/reset")
        st.session_state.run_id = None
    st.success("Reset done")

if st.button("State of Producer"):
    with st.spinner("Loading producer state..."):
        response = get_status()
        st.json(response)
    