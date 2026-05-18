predictive-maintenance-platform/

│
├── README.md

├── docker-compose.yml

│

├── config/
│ ├── settings.py
│ └── logging.yaml
│

├── data/
│ ├── raw/
│ │ ├── train_FD001.txt
│ │ ├── test_FD001.txt
│ │ └── RUL_FD001.txt
│ │
│ ├── processed/
│ └── scalers/
│

├── notebooks/
│ ├── eda.ipynb
│ ├── feature_engineering.ipynb
│ └── training.ipynb
│

├── streaming/
│ ├── replay_engine.py
│ ├── stream_manager.py
│ ├── websocket_client.py
│ └── event_generator.py
│

├── backend/
│ ├── main.py
│ ├── websocket.py
│ ├── routes/
│ │ ├── prediction_routes.py
│ │ └── engine_routes.py
│ │
│ ├── services/
│ │ ├── inference_service.py
│ │ ├── preprocessing_service.py
│ │ └── alert_service.py
│ │
│ └── schemas/
│ ├── sensor_schema.py
│ └── prediction_schema.py
│

├── models/
│ ├── training/
│ │ ├── train_lstm.py
│ │ ├── train_gru.py
│ │ └── train_transformer.py
│ │
│ ├── inference/
│ │ ├── lstm_inference.py
│ │ ├── transformer_inference.py
│ │ └── model_registry.py
│ │
│ ├── saved_models/
│ │ ├── lstm_fd001.pt
│ │ └── transformer_fd001.pt
│ │
│ └── utils/
│ ├── dataset.py
│ ├── windowing.py
│ └── metrics.py
│

├── dashboard/
│ ├── app.py
│ ├── layouts/
│ │ ├── overview.py
│ │ ├── live_monitoring.py
│ │ ├── predictions.py
│ │ └── analytics.py
│ │
│ ├── components/
│ │ ├── sensor_chart.py
│ │ ├── rul_gauge.py
│ │ ├── health_indicator.py
│ │ └── anomaly_table.py
│ │
│ └── assets/
│ └── style.css
│

├── kafka/
│ ├── producer.py
│ ├── consumer.py
│ └── topics.md
│
├── database/
│ ├── postgres.sql
│ └── timeseries_schema.sql
│

└── deployment/
├── Dockerfile.backend
├── Dockerfile.dashboard
├── Dockerfile.model
