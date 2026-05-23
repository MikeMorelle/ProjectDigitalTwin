"""
predict_example.py
Demo script to test the anomaly detection model on FD001 test data.
Run: python predict_example.py
"""

import joblib
import pandas as pd
import numpy as np
import sys

# Column names for NASA data
COLUMN_NAMES = [
    'unit_id', 'cycle', 'op_setting_1', 'op_setting_2', 'op_setting_3',
    'sensor_1', 'sensor_2', 'sensor_3', 'sensor_4', 'sensor_5',
    'sensor_6', 'sensor_7', 'sensor_8', 'sensor_9', 'sensor_10',
    'sensor_11', 'sensor_12', 'sensor_13', 'sensor_14', 'sensor_15',
    'sensor_16', 'sensor_17', 'sensor_18', 'sensor_19', 'sensor_20', 'sensor_21'
]

print("Loading model...")
bundle = joblib.load('anomaly_detection_model.joblib')

model          = bundle['model']
scalers        = bundle['scalers']
cluster_models = bundle['cluster_models']
feature_cols   = bundle['feature_cols']
sensor_cols    = bundle['sensor_cols']
window         = bundle['rolling_window']

print(f"Model: Isolation Forest (contamination={bundle['config']['contamination']})")
print(f"Features: {len(feature_cols)}")
print()

# Check if user provided a data file
if len(sys.argv) > 1:
    data_file = sys.argv[1]
else:
    data_file = input("Enter path to NASA test file (e.g., test_FD001.txt): ")

# Load data
print(f"Loading: {data_file}")
data = pd.read_csv(data_file, sep='\s+', header=None, names=COLUMN_NAMES)
data = data.sort_values(['unit_id', 'cycle']).reset_index(drop=True)

# Detect which dataset (FD001-FD004)
dataset_num = int(data_file.split('FD00')[1][0])
print(f"Detected: FD00{dataset_num}")

# Preprocess
if dataset_num in [2, 4]:
    print("Applying 6-cluster normalization...")
    data['cluster'] = cluster_models[dataset_num].predict(
        data[['op_setting_1', 'op_setting_2', 'op_setting_3']]
    )
    for cid in range(6):
        mask = data['cluster'] == cid
        if mask.sum():
            data.loc[mask, sensor_cols] = scalers[dataset_num][cid].transform(
                data.loc[mask, sensor_cols].astype(float)
            )
else:
    print("Applying single-condition normalization...")
    data[sensor_cols] = scalers[dataset_num].transform(data[sensor_cols].astype(float))

# Rolling features
print("Computing rolling features...")
for engine in data['unit_id'].unique():
    mask = data['unit_id'] == engine
    for sensor in sensor_cols:
        data.loc[mask, f'{sensor}_roll_mean'] = data.loc[mask, sensor].rolling(window=window, min_periods=1).mean().values
        data.loc[mask, f'{sensor}_roll_std']  = data.loc[mask, sensor].rolling(window=window, min_periods=1).std().values

# Predict
print("Predicting anomalies...")
data['anomaly_score'] = model.decision_function(data[feature_cols])
data['is_anomaly']    = (model.predict(data[feature_cols]) == -1).astype(int)

# Warmup fix
for engine in data['unit_id'].unique():
    mask = data['unit_id'] == engine
    data.loc[mask & (data['cycle'] <= window), 'is_anomaly'] = 0

# Results
total_anomalies = data['is_anomaly'].sum()
total_cycles    = len(data)
print()
print("=" * 50)
print("RESULTS")
print("=" * 50)
print(f"Total cycles:     {total_cycles:,}")
print(f"Anomalies found:  {total_anomalies:,} ({total_anomalies/total_cycles*100:.1f}%)")
print(f"Score range:      {data['anomaly_score'].min():.3f} to {data['anomaly_score'].max():.3f}")
print()
print("Sample (first 10 rows):")
print(data[['unit_id', 'cycle', 'anomaly_score', 'is_anomaly']].head(10).to_string(index=False))

# Save results
output_file = f'predictions_FD00{dataset_num}.csv'
data[['unit_id', 'cycle', 'anomaly_score', 'is_anomaly']].to_csv(output_file, index=False)
print(f"\nResults saved to: {output_file}")