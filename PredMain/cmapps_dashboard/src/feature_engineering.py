import pandas as pd

#Window size for rolling features
WINDOW = 30

def build_window_features(window):
    """Build rolling features for a given window of sensor data."""
    row = {}

    for sensor in window.columns:
        row[f'{sensor}_mean'] = window[sensor].mean()
        row[f'{sensor}_std'] = window[sensor].std()
        row[f'{sensor}_trend'] = window[sensor].iloc[-1] - window[sensor].iloc[0]

    return row
