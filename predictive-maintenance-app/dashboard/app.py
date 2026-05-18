import streamlit as st
import websocket
import threading
import json
import time

st.title("Live Sensor Dashboard")

data = []

def on_message(ws, message):
    global data
    msg = json.loads(message)
    data.append(msg["value"])

def run_ws():
    ws = websocket.WebSocketApp(
        "ws://backend:8000/ws",
        on_message=on_message
    )
    ws.run_forever()

threading.Thread(target=run_ws, daemon=True).start()

chart = st.empty()

while True:
    chart.line_chart(data)
    time.sleep(1)