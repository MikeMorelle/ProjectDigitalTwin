import asyncio
import websockets
import json
import random
import time

uri = "ws://backend:8000/ws"

async def stream():

    print("STARTING STREAM")

    while True:
        try:
            print("Connecting...")

            async with websockets.connect(uri) as ws:

                await ws.send(json.dumps({"value": 3}))

                await asyncio.sleep(1)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(3)

print("SCRIPT LOADED")  

asyncio.run(stream())