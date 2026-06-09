CREATE TABLE IF NOT EXISTS anomaly_results (
    id SERIAL PRIMARY KEY,
    engine_id INT,
    cycle INT,
    anomaly_score FLOAT,
    is_anomaly INT,
    timestamp TIMESTAMP DEFAULT NOW()
);