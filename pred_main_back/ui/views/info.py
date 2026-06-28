import streamlit as st
from db.db_client import fetch_latest_cycle_per_engine
import requests

st.title("Test")

if "run_id" not in st.session_state:
    try:
        status = requests.get("http://api:8000/status").json()
        st.session_state.run_id = status.get("run_id")
    except:
        st.write("Start run first!")

df = fetch_latest_cycle_per_engine(st.session_state.run_id)
st.dataframe(df)
