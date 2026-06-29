import streamlit as st


setup = st.Page(
    "views/setup.py",
    title="Setup"
)

info = st.Page(
    "views/info.py",
    title="Information"
)

dashboard = st.Page(
    "views/dashboard.py",
    title="Dashboard"
)

unchanged_sensors = st.Page(
    "views/unchanged_sensors.py",
    title="Unchanged sensors"
)

pg = st.navigation([
    setup,
    info, 
    dashboard,
    unchanged_sensors
])

pg.run()

