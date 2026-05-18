import streamlit as st
import websocket
import threading
import json
import time

st.title("Sensor Stream")

sensor_values = []
chart = st.empty()

def on_message(ws, message):

    data = json.loads(message)

    sensor_values.append(data["value"])


def run_ws():

    ws = websocket.WebSocketApp(
        "ws://backend:8000/ws",
        on_message=on_message
    )

    ws.run_forever()

threading.Thread(target=run_ws, daemon=True).start()

while True:
    chart.line_chart(sensor_values)
    time.sleep(1)