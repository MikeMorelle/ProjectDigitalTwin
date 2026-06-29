from fastapi import FastAPI
from kafka_manager.stream_manager import StreamManager, ProducerConfig
from kafka_manager.producer import Producer
from db.db_client import fetch_engine_history
import uvicorn
from ml.models.isolation_forest import IsolationForestModel
import shapiq

iso_model = IsolationForestModel()
explainer = shapiq.TreeExplainer(model=iso_model.model, index="k-SII", min_order=1, max_order=3)
TOP_K = 5

manager = StreamManager(producer=Producer())
app = FastAPI()

#Fast-API 
@app.post("/start")
def start(req: ProducerConfig):
    config = ProducerConfig(
        dataset=req.dataset,
        interval=req.interval,
        fault_config=req.fault_config
    )

    manager.start(config)

    return manager.status()

@app.get("/status")
def status():
    return manager.status()
    
@app.post("/reset")
def reset():
    manager.stop()

    return {"status": "reset_done"}
    
#https://www.aidancooper.co.uk/a-non-technical-guide-to-interpreting-shap-analyses/
#https://www.esann.org/sites/default/files/proceedings/2025/ES2025-163.pdf
@app.post("/explain/shap")
def explain(run_id:str, engine_id:int, dataset_num:str):
    iso_model.clear()
    X = None
    
    data = fetch_engine_history(engine_id, run_id)

    if len(data) == 0:
        print("No data fetched for explaining", flush = True)
    
    for _, row in data.iterrows():
        engine = {
            "engine_id": engine_id,
            "sensors": row["sensors"],
            "ops": row["ops"]
        }

        X = iso_model.build_feature_vector(engine, dataset_num)
    
    explanation = explainer.explain(X.values[0])
    feature_names = iso_model.feature_cols

    single = []
    interactions = []

    vals_1_order = explanation.get_n_order_values(1)

    for i, f in enumerate(feature_names):
        single.append({
            "feature": f,
            "value": float(vals_1_order[i])
        })
    single = sorted(single, key=lambda x: abs(x["value"]), reverse=True)[:TOP_K]
    
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)