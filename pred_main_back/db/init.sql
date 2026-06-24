CREATE TABLE IF NOT EXISTS sensor_data (
    engine_id INT NOT NULL,
    cycle INT NOT NULL,
    ops JSONB NOT NULL,
    sensors JSONB NOT NULL,
    anomaly_score DOUBLE PRECISION,
    is_anomaly BOOLEAN,
    rul REAL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (engine_id, cycle)
);