import streamlit as st
import pandas as pd
import plotly.express as px
import time
from streamlit_autorefresh import st_autorefresh

#Congig
st.set_page_config(page_title="CMAPPS Dashboard", layout="wide")

#Placeholder for dynamic content
placeholder = st.empty()

#Load data
index_names = ['unit_num', 'time_cycles']
setting_names = ['setting1', 'setting2', 'setting3']
sensor_names = ['sensor{}'.format(i) for i in range(1, 22)]
col_names = index_names + setting_names + sensor_names
train = pd.read_csv("../data/train_FD001.txt", sep='\s+', header=None, names=col_names)

#load history data for SHAP values and RUL predictions
history = pd.read_csv("../output/history.csv")
history["time"] = pd.to_datetime(history["time"])
shap_cols = [col for col in history.columns if col not in ["engine_id", "time", "predicted_rul"]]

#Melt the history data for plotting
melted = history.melt(id_vars=["time"], value_vars=shap_cols, var_name="feature", value_name="importance")
fig = px.line(melted, x="time", y="importance", color="feature", title="Sensor Data")

#Get the latest values for each feature
latest_pred = (melted.groupby("feature").tail(1))
latest_rul = history["predicted_rul"].iloc[-1]
latest_cycle = history["time"].iloc[-1]

#Display the dashboard
with placeholder.container():
    #create two columns for metrics and SHAP values
    c1, c2 = st.columns([3,1])

    with c1: 
        st.metric(label="Latest Predicted RUL", value=f"{latest_rul:.2f}", delta=None)
        st.metric(label="Latest Cycle Time", value=latest_cycle.strftime("%H:%M:%S"), delta=None)

    with c2:
        st.dataframe(
            latest_pred[["feature", "importance"]],
            use_container_width=True
        )

    #get warning if there is an error loading the data or plotting
    try:
        pass

    except Exception as e:
        st.warning(f"Error loading data: {e}")

#Autorefresh page every 10 seconds    
st_autorefresh(interval=10000, key="refresh")