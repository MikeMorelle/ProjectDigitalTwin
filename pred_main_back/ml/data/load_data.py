import pandas as pd
from config import SENSORS
from pathlib import Path


def load_data(ds_name):
    test_path = Path(f"ml/data/test_{ds_name}.txt")
    rul_path = Path(f"ml/data/RUL_{ds_name}.txt")

    if not test_path.exists() or not rul_path.exists():
        raise FileNotFoundError(
            "Dataset not found"
        )

    df = pd.read_csv(test_path, sep=r"\s+", header=None)
    df.columns = ["engine_id", "cycle", "op_1", "op_2", "op_3"] + SENSORS

    rul = pd.read_csv(rul_path, header=None).values.flatten()

    #last cycle per engine
    last_cycle = df.groupby("engine_id")["cycle"].max()

    #map engine to failure
    failure_map = last_cycle + rul
    df["failure_cycle"] = df["engine_id"].map(failure_map)

    df["true_rul"] = df["failure_cycle"] - df["cycle"]
    df.drop(columns=["failure_cycle"], inplace=True)

    return df

def load_test(ds_name):
    path = Path(f"ml/data/train_{ds_name}.txt")

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )
    df = pd.read_csv(path, sep=r"\s+", header=None)
    df.columns = ["engine_id", "cycle", "op1", "op2", "op3"] + SENSORS
    return df
