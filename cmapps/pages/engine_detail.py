import streamlit as st
import pandas as pd
import joblib
from components import prep_data, read_data, turbofan
import plotly.express as px
import shap
import numpy as np


st.title("Engine Detail")

#read data and prepate data point, names and 
df = read_data.prepare()
latest, sensor_cols, X_scaled = prep_data.get_stats(df)

selected_engine = st.selectbox("Select Engine", df["unit_num"].unique())

latest["status"] = latest["status"].astype(str)
engine_data = latest[
    latest['unit_num'] == selected_engine
].iloc[0]


st.header(f"Engine {selected_engine} Detail Report")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Predicted RUL",
        round(engine_data['pred_RUL'],1)
    )

with col2:
    st.metric(
        "Failure Probability",
        f"{round(engine_data['failure_prob']*100,1):.2f}%"
    )

with col3:
    st.metric(
        "Status",
        engine_data['status']
    )


st.subheader("Maintenance Recommendation")

if engine_data['failure_prob'] > 0.7:
    st.error(
        "Immediate inspection recommended. "
        "High degradation detected."
    )

elif engine_data['failure_prob'] > 0.4:
    st.warning(
        "Schedule maintenance within next cycles."
    )

else:
    st.success(
        "Engine operating normally."
    )

st.subheader("Sensor Trends")

engine_history = df[df['unit_num'] == selected_engine]

selected_sensors = st.multiselect(
    "Select Sensors",
    sensor_cols,
    default=sensor_cols[10]
)

for sensor in selected_sensors:

    fig = px.line(
        engine_history,
        x='cycle',
        y=sensor,
        template='plotly_dark',
        title=f"{sensor} Trend"
    )

    st.plotly_chart(
        fig,
        width='stretch'
    )

model = joblib.load("models/xgb_rul_model.pkl")
feature_cols = joblib.load("models/features.pkl")

explainer = shap.TreeExplainer(model)

shap_values = explainer.shap_values(X_scaled)

engine_idx = latest.index[latest["unit_num"] == selected_engine][0]
sv = shap_values[engine_idx]

shap_df = pd.DataFrame({
    "feature": feature_cols,
    "importance": np.abs(sv)
})

shap_df = shap_df.sort_values(
    'importance',
    ascending=False
).head(10)

fig = px.bar(
    shap_df,
    x='importance',
    y='feature',
    orientation='h',
    template='plotly_dark',
    title='Top Contributing Sensors'
)

st.plotly_chart(
    fig,
    width='stretch'
)

import streamlit as st

highlight = st.selectbox(
    "Komponente auswählen",
    ["None", "Fan", "LPC", "HPC", "Combustor", "HPT", "LPT", "Nozzle"]
)

def color(part):
    return "red" if highlight == part else "#1f77b4"

