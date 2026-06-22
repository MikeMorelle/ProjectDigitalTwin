import threading
import uuid
from db.db_client import reset_database
from fastapi import FastAPI
from pydantic import BaseModel
from kafka_manager.state_manager import StreamManager, ProducerConfig
from kafka_manager.producer import Producer
from db.db_client import reset_database
import uvicorn

manager = StreamManager(producer=Producer())
app = FastAPI()

#Fast-API 
@app.post("/start")
def start(req: ProducerConfig):
    config = ProducerConfig(
        dataset=req.dataset,
        interval=req.interval
    )

    manager.start(config)

    return manager.status()

@app.get("/status")
def status():
    return manager.status()
    
@app.post("/reset")
def reset():
    manager.stop()
    
    reset_database()

    return {"status": "reset_done"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
