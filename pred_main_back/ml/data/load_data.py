import pandas as pd
from pathlib import Path

from config import SENSORS, OPS

#for loading test/RUL datasets
def load_test(ds_name):
    test_path = Path(f"ml/data/test_{ds_name}.txt")
    rul_path = Path(f"ml/data/RUL_{ds_name}.txt")

    if not test_path.exists() or not rul_path.exists():
        raise FileNotFoundError(
            "Dataset not found"
        )

    #load into pandas dataframe and set column names
    df = pd.read_csv(test_path, sep=r"\s+", header=None)
    df.columns = ["engine_id", "cycle"] + OPS + SENSORS

    rul = pd.read_csv(rul_path, header=None).values.flatten()

    #last cycle per engine
    last_cycle = df.groupby("engine_id")["cycle"].max()

    #map engine to failure
    failure_map = last_cycle + rul
    df["failure_cycle"] = df["engine_id"].map(failure_map)

    #append true RUL column to the dataframe
    df["true_rul"] = df["failure_cycle"] - df["cycle"]
    df.drop(columns=["failure_cycle"], inplace=True)

    return df

#for loading training datasets
def load_data(ds_name):
    path = Path(f"ml/data/train_{ds_name}.txt")

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )
    
    #load into pandas dataframe and set column names
    df = pd.read_csv(path, sep=r"\s+", header=None)
    df.columns = ["engine_id", "cycle"] + OPS + SENSORS
    
    #failure = last cycle per engine -> used to calculate true RUL for each row
    last_cycle = df.groupby("engine_id")["cycle"].transform("max")
    df["true_rul"] = last_cycle - df["cycle"]

    return df
