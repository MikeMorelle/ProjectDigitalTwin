from fastapi import FastAPI
import shapiq
import uvicorn

from kafka_manager.stream_manager import StreamManager, ProducerConfig
from kafka_manager.producer import Producer
from db.db_client import fetch_engine_history
from ml.models.isolation_forest import IsolationForestModel

#load own model
iso_model = IsolationForestModel()
#load tree explainer which uses k-subset interaction index (k-SII) to compute feature contributions and interactions up to 2nd order -> only take top 5 influences 
explainer = shapiq.TreeExplainer(model=iso_model.model, index="k-SII", min_order=1, max_order=2)
TOP_K=5

#load manager for kafka streaming and attach kafka producer for flexibility in data generation
manager = StreamManager(producer=Producer())

#fastAPI as communication between front- and backend
app = FastAPI()

#start streaming data from kafka producer with given configuration
@app.post("/start")
def start(req: ProducerConfig):
    config = ProducerConfig(
        dataset=req.dataset,
        interval=req.interval,
        fault_config=req.fault_config
    )

    manager.start(config)

    return manager.status()

#get status of the streaming process, incl. is_running, run_id, dataset, interval, and fault configuration
@app.get("/status")
def status():
    return manager.status()

#stop streaming data from kafka producer
@app.post("/reset")
def reset():
    manager.stop()

    return {"status": "reset_done"}

#explain the feature contributions and interactions of the given engine_id and run_id with the trained isolation forest model    
@app.post("/explain/shap")
def explain(run_id:str, engine_id:int, dataset_num:str):
    #reset rolling features to avoid contamination from previous runs
    iso_model.clear()
    #X variable for rebuilding feature vector
    X = None
    
    data = fetch_engine_history(engine_id, run_id)

    if len(data) == 0:
        print("No data fetched for explaining", flush = True)
    
    #build feature vector for each row in the latest data
    for _, row in data.iterrows():
        engine = {
            "engine_id": engine_id,
            "sensors": row["sensors"],
            "ops": row["ops"]
        }

        X = iso_model.build_feature_vector(engine, dataset_num)
    
    #as X in shape (1, n_features) -> use only 1D vector for explanation
    explanation = explainer.explain(X.values[0])
    feature_names = iso_model.feature_cols

    single = []
    interactions = []

    #first order for feature contributions 
    vals_1_order = explanation.get_n_order_values(1)

    for i, f in enumerate(feature_names):
        single.append({
            "feature": f,
            "value": float(vals_1_order[i])
        })
    single = sorted(single, key=lambda x: abs(x["value"]), reverse=True)[:TOP_K]

    #2nd order for feat interactions
    vals_2_order = explanation.get_n_order_values(2)

    for i in range(len(feature_names)):
        for j in range(i+1, len(feature_names)):
            interactions.append({
                "features": [feature_names[i], feature_names[j]],
                "value": float(vals_2_order[i][j])
            })

    interactions = sorted(interactions, key=lambda x: abs(x["value"]), reverse=True)[:TOP_K]
    
    return {
        "feature_contributions": single,
        "feature_interactions": interactions
    }

#run the fastAPI server on host
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)