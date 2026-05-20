import streamlit as st
from components import turbofan 

st.set_page_config(layout="wide")

#critical, ok & warning....find component id's in turbofan.py
status = {
    "LPC": "ok",
    "HPC": "ok",
    "N2": "ok"
}

st.iframe(turbofan.build_css(status) + turbofan.svg, height=500, width=2000)
