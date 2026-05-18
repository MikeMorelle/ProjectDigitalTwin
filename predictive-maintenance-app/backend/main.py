from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# WebSocket server to broadcast messages to all connected clients
app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# WebSocket endpoint for clients to connect and receive real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    #add client to list of connected clients
    await manager.connect(websocket)

    #keep connection open and broadcast received messages to all clients
    try: 
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)

    #remove client from list if connection is closed or an error occurs
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("WebSocket connection closed:")