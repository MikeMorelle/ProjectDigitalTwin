CREATE TABLE IF NOT EXISTS anomaly_results (
    engine_id INT,
    cycle INT,
    anomaly_score FLOAT,
    is_anomaly INT,
    rul FLOAT,
    timestamp TIMESTAMP DEFAULT NOW()
);