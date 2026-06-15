import psycopg2, time, pandas as pd, os
from sqlalchemy import create_engine
from config import POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, POSTGRES_HOST, POSTGRES_PORT

#for later to not get warn
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

def insert_result(conn, row):
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO anomaly_results (
            engine_id,
            cycle,
            anomaly_score,
            is_anomaly,
            rul
        ) VALUES (%s, %s, %s, %s, %s)
    """, (
        row["engine_id"],
        row["cycle"],
        row["anomaly_score"],
        row["is_anomaly"],
        row["rul"]
    ))

    conn.commit()

def fetch_latest_cycle_per_engine():
    df = pd.read_sql("""
        SELECT *
        FROM anomaly_results ar
        WHERE cycle = (
            SELECT MAX(cycle) 
            FROM anomaly_results
            WHERE engine_id = ar.engine_id)
        ORDER BY engine_id
    """, engine)

    return df

