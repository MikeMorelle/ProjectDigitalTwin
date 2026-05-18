import asyncio
import websockets
import json
import time 

uri = "ws://backend:8000/ws"

async def stream():
    while True:
        try: 
            print("Connecting to WebSocket server...")
            async with websockets.connect(uri) as ws:
                print("Connected to WebSocket server. Starting to send data...")
                while True:
                        await ws.send(json.dumps({"value": 3}))
                        await asyncio.sleep(2)

        except Exception as e:
            print("WebSocket error:", e)
            await asyncio.sleep(3)  

if __name__ == "__main__":
    asyncio.run(stream())