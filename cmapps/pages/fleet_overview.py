import streamlit as st
import pandas as pd
import numpy as np
import joblib
import shap
import plotly.express as px
import plotly.graph_objects as go
from components import prep_data, read_data


model = joblib.load("models/xgb_rul_model.pkl")
scaler = joblib.load("models/scaler.pkl")
feature_cols = joblib.load("models/features.pkl")

df = read_data.prepare()
latest, sensor_cols, X_scaled = prep_data.get_stats(df)

col1, col2, col3, col4 = st.columns(4)

critical_count = len(
    latest[latest["status"] == "Critical"] 
)

with col1:
    st.metric("Total Engines", len(latest))

with col2:
    st.metric("Critical Engines", critical_count)

with col3:
    st.metric(
        "Average RUL",
        round(latest["pred_RUL"].mean(),1)
    )

with col4:
    st.metric(
        "Average Health Score",
        f"{round(latest['health_score'].mean(),1):.2f}%"
    )
st.divider()

st.subheader("Fleet Overview")
overview = latest[[
    "unit_num",
    "pred_RUL",
    "failure_prob",
    "health_score",
    "status"
]
]

cols = st.columns(10)

for i, row in overview.iterrows():
    with cols[i%10]:
                st.markdown(
            f"""
            <div style="
                border: 2px solid #00c853;
                border-radius: 10px;
                padding: 10px;
                margin: 5px;
                text-align: center;
                background-color: #00000;
            ">
                <b>{row['unit_num']}</b><br>
                {row['status']}
            </div>
            """,
            unsafe_allow_html=True
        )

col1, col2 = st.columns(2)

with col1:
    fig = px.histogram(
        latest,
        x="failure_prob",
        nbins=20,
        title="Failure Probability Distribution",
        template="plotly_dark"
    )

    st.plotly_chart(
        fig, 
        width='stretch'
    )

with col2:
    fig2 = px.scatter(
        latest,
        x="pred_RUL",
        y="failure_prob",
        color="status",
        title="RUL vs Failure Probability",
        template="plotly_dark"
    )
    st.plotly_chart(
        fig2, 
        width='stretch'
    )

st.divider()
