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

pg = st.navigation([
    setup,
    info, 
    dashboard
])

pg.run()

