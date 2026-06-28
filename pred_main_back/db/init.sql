CREATE TABLE IF NOT EXISTS sensor_data (
    run_id UUID NOT NULL,
    engine_id INT NOT NULL,
    cycle INT NOT NULL,
    ops JSONB NOT NULL,
    sensors JSONB NOT NULL,
    true_rul INT NOT NULL,
    anomaly_score DOUBLE PRECISION,
    is_anomaly BOOLEAN,
    rul REAL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (run_id,engine_id, cycle)
);