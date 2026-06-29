import streamlit as st
import requests
from db.db_client import fetch_latest_cycle_per_engine

st.title("Test")

try:
        status = requests.get("http://api:8000/status").json()
        run_id = status.get("run_id")
        dataset_num = status.get("dataset")
        df = fetch_latest_cycle_per_engine(run_id)
        st.write("Du bekommst folgende Werte im Datensatz: ", df.columns.tolist())
        
        #Beispiel, wie SHAP Werte abgefragt werden können. Es dauert etwas, da es sehr rechenaufwendig ist. Du bekommst einzelne Haupteinflussfaktoren und interagierende/Paare
        with st.spinner("Warte auf SHAP Werte..."):
                params= {
                "run_id": run_id,
                "engine_id": 7,     #derzeit festgesetzt, kann aber beliebig für UI verändert werden
                "dataset_num": dataset_num
                }

                response = requests.post("http://api:8000/explain/shap", params=params)

                explanations =  response.json()

                st.write(explanations)

except Exception as e:
        st.write("Wait for Stream")



