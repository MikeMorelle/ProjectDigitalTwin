from fastapi import FastAPI, WebSocket

# WebSocket server to broadcast messages to all connected clients
app = FastAPI()
clients = set()

# WebSocket endpoint for clients to connect and receive real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    #add client to list of connected clients
    await websocket.accept()
    clients.add(websocket)

    #keep connection open and broadcast received messages to all clients
    try: 
        while True:
            data = await websocket.receive_text()
            print(f"Received data: {data}")
            
            for client in clients:
                await client.send_text(data)

    #remove client from list if connection is closed or an error occurs
    except Exception as e:
        print(f"WebSocket error: {e}")

    finally:
        clients.remove(websocket)