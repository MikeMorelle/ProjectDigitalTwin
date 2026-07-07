# pages/Info.py

import streamlit as st

st.set_page_config(
    page_title="Predictive Maintenance - Information",
    layout="wide"
)

st.title("Predictive Maintenance Monitoring System")

st.markdown("""
## Overview

This dashboard provides real-time monitoring of a fleet of NASA turbofan engines.
Incoming sensor data is continuously analyzed to detect abnormal behavior
and support predictive maintenance decisions.

The system combines:

- **Live data streaming**
- **Anomaly detection using Isolation Forest**
- **Remaining Useful Life (RUL) estimation using LSTM**
- **SHAP-based model explanations**
- **Historical sensor analysis**

The goal is to identify potential failures early and enable
condition-based maintenance instead of reactive repairs.
""")

st.divider()

st.header("Engine Status")

st.markdown("""
Each engine can have one of the following states:

| Status | Meaning |
|---|---|
| ⚪ Initializing | Not enough data is available for reliable evaluation |
| 🟢 Normal | The model detects normal operating behavior |
| 🔴 Anomaly | The model detects abnormal behavior |

### Initialization Phase

To avoid unreliable predictions, an engine is not classified immediately
after startup.

The first operating cycles are used to collect sufficient historical
information and establish a reference for normal behavior.

Only after enough cycles are available, anomaly detection becomes active.
""")

st.divider()

st.header("Isolation Forest Anomaly Detection")

st.markdown("""
The Isolation Forest is a machine learning algorithm used to identify unusual
patterns in data.

The idea behind the algorithm:

- Normal operating states are similar to many other observations.
- Anomalies are different and can be isolated more easily.

The anomaly score represents how strongly the current engine condition
deviates from normal behavior.
""")

st.divider()

st.header("LSTM Remaining Useful Life (RUL)")

st.markdown("""
Remaining Useful Life (RUL) estimates how many operational cycles remain
before an engine reaches the end of its expected lifetime.

A reliable RUL estimation requires enough historical observations.

Therefore:

- During the initial learning phase, RUL is not displayed.
- After sufficient historical data is available, the estimated remaining
  lifetime is shown.

Before the prediction becomes available, the dashboard displays:

> Collecting data...

This prevents unreliable early predictions.
""")

st.divider()

st.header("SHAP Model Explanation")

st.markdown("""
SHAP explains why the machine learning model produced a specific prediction.

The explanation contains two main parts:

## Top SHAP Drivers

These are individual features that have the strongest influence on the
model output.

Example:

🟢 **Average of sensor 4 reduces anomaly likelihood**

Meaning:

The current behavior of this sensor supports a normal operating condition.

---

🔴 **Average of sensor 7 increases anomaly likelihood**

Meaning:

This sensor behavior pushes the model decision towards an anomaly.

---

## SHAP Feature Interactions

Interactions describe combinations of features that influence the prediction
together.

The combination of both sensor behaviors provides additional information to
the model beyond the individual sensor contributions.
""")

st.divider()

st.header("Dashboard Features")

st.markdown("""
## Fleet Overview

Provides a high-level view of all monitored engines:

- Total number of engines
- Number of normal engines
- Number of detected anomalies


## Engine Detail View

For each engine, the dashboard provides:

- Current cycle
- Anomaly score
- Remaining Useful Life estimation
- Historical anomaly trends
- Sensor trends
- Baseline deviation analysis
- SHAP explanations
""")

st.divider()

st.header("User Workflow")

st.markdown("""
Recommended workflow:

0. Start a dataset streaming in the setup page (accessible on the left). Choose a dataset, time interval in which it should be streamed and optionally a bias.
1. Monitor the **Fleet Overview** for engines with abnormal states in dahsboard view (accessible on the left).
2. Open the corresponding **Engine Detail View**.
3. Review:
   - anomaly score trends
   - sensor behavior
   - baseline deviations
4. Use **SHAP explanations** to identify the main contributing factors.
5. Use the information to support maintenance decisions.
(Optional) Use the unchanged sensors view (accessible on the left) to reconsider redundant sensor placements, as they can negatively affect the ML models.
""")
