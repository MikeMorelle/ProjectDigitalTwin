import pandas as pd
from config import SENSORS
from pathlib import Path


def load_data(ds_name):
    path = Path(f"ml/data/train_{ds_name}.txt")

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )
    df = pd.read_csv(path, sep=r"\s+", header=None)
    df.columns = ["engine_id", "cycle", "op_1", "op_2", "op_3"] + SENSORS
    return df
