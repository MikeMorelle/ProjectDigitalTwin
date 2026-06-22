import threading
import uuid
from db.db_client import reset_database
from fastapi import FastAPI
from pydantic import BaseModel
from sensor_stream_producer.state_manager import state
from sensor_stream_producer.producer import produce_dataset
from db.db_client import reset_database
import uvicorn

app = FastAPI()

class StartRequest(BaseModel):
    dataset: str
    interval: int

#Fast-API 
@app.post("/start")
def start(req: StartRequest):
    if state.running.is_set():
        return {"status": "already_running"}
    
    state.running.set()
    run_id = str(uuid.uuid4())
    state.current_id = run_id
    state.current_ds = req.dataset
    state.interval = req.interval
    
    thread = threading.Thread(
        target=produce_dataset,
        args=(req.dataset,req.interval),
        daemon=True
    )
    thread.start()
    state.current_thread = thread

    return {
        "status": "started",
        "run_id": run_id,
        "dataset": req.dataset,
        "interval": req.interval
    }

@app.get("/status")
def status():
    return {
        "running": state.running.is_set(),
        "dataset": state.current_ds,
        "run_id": state.current_id,
        "interval": state.interval
    }
    
@app.post("/reset")
def reset():
    state.running.clear()
    state.current_id = None
    state.current_ds = None
    state.interval = None
    
    reset_database()

    return {"status": "reset_done"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
