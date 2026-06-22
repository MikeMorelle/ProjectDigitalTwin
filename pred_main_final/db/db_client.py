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
        INSERT INTO sensor_data (engine_id, cycle, ops, sensors) 
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (engine_id, cycle)
        DO UPDATE SET
            ops = EXCLUDED.ops,
            sensors = EXCLUDED.sensors,
            timestamp = NOW()
    """
    rows = [
        (
            e["engine_id"],
            cycle,
            json.dumps(e["ops"]),
            json.dumps(e["sensors"])
        )
        for e in engines
    ]

    with conn.cursor() as cur:
        execute_batch(cur, sql, rows)

    conn.commit()

def fetch_latest_cycle_per_engine():
    df = pd.read_sql("""
        SELECT DISTINCT ON (engine_id) * 
        FROM sensor_data
        ORDER BY engine_id, cycle DESC;
    """, engine)

    return df

def reset_database():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("TRUNCATE TABLE sensor_data;")
        conn.commit()
    finally:
        conn.close()

