import pandas as pd
from config import SENSORS

def load_data():
    df = pd.read_csv("ml/data/train_FD001.txt", sep=r"\s+", header=None)
    df.columns = ["engine_id", "cycle", "op1", "op2", "op3"] + SENSORS
    return df
