from config import SENSORS, ROLLING_WINDOW_SIZE


def add_rolling_features(df):
    df = df.sort_values(["engine_id", "cycle"]).copy()

    rolling_features = []

    for s in SENSORS:
        mean_col = f"{s}_rolling_mean"
        std_col = f"{s}_rolling_std"

        df[mean_col] = (
            df.groupby("engine_id")[s]
              .rolling(window=ROLLING_WINDOW_SIZE, min_periods=1)
              .mean()
              .reset_index(level=0, drop=True)
        )
        df[std_col] = (
            df.groupby("engine_id")[s]
              .rolling(window=ROLLING_WINDOW_SIZE, min_periods=2)
              .std()
              .fillna(0.0)
              .reset_index(level=0, drop=True)
        )
        rolling_features.extend([mean_col, std_col])

    df = df[rolling_features]
        
    return df