import psycopg2, time, pandas as pd, os
from sqlalchemy import create_engine
from config import POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, POSTGRES_HOST, POSTGRES_PORT
import json
from psycopg2.extras import execute_batch

engine = create_engine(
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

def get_connection():
    while True:
        try:
            conn = psycopg2.connect(
                dbname=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                host=POSTGRES_HOST,
                port=POSTGRES_PORT
            )
            return conn
        except Exception as e:
            print("DB connection error:", e)
            time.sleep(5)

def insert_batch(conn, cycle, engines):

    sql = """
        INSERT INTO sensor_data (run_id, engine_id, cycle, ops, sensors, true_rul, anomaly_score, is_anomaly, rul) 
        VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (run_id, engine_id, cycle)
        DO UPDATE SET
            ops = EXCLUDED.ops,
            sensors = EXCLUDED.sensors,
            anomaly_score = EXCLUDED.anomaly_score,
            is_anomaly = EXCLUDED.is_anomaly,
            rul = EXCLUDED.rul,
            timestamp = NOW()
    """
    rows = [
        (
            e["run_id"],
            e["engine_id"],
            cycle,
            json.dumps(e["ops"]),
            json.dumps(e["sensors"]),
            e.get("true_rul"),
            e.get("anomaly_score"),
            e.get("is_anomaly"),
            e.get("rul")
        )
        for e in engines
    ]

    with conn.cursor() as cur:
        execute_batch(cur, sql, rows)

    conn.commit()

def fetch_latest_cycle_per_engine(run_id):
    df = pd.read_sql(f"""
        SELECT DISTINCT ON (engine_id) * 
        FROM sensor_data
        WHERE run_id = %(run_id)s
        ORDER BY engine_id, cycle DESC;
    """, engine, params={"run_id": run_id})

    return df


def fetch_engine_history(engine_id, run_id):
    """
    Return all cycles for one engine from sensor_data, ordered by cycle.
    Used by the dialog to draw trend charts (anomaly score & RUL over time).
    """
    eid = int(engine_id)  # convert numpy.int64 → plain Python int
    df = pd.read_sql("""
        SELECT engine_id, cycle, ops, sensors, anomaly_score, rul
        FROM sensor_data
        WHERE engine_id = %(eid)s
        AND run_id = %(run_id)s
        ORDER BY cycle
    """, engine, params={"eid": eid, "run_id": run_id})
    return df


