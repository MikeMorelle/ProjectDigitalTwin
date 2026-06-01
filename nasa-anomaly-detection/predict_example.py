"""
predict_example.py
Demo script to test the anomaly detection model on NASA CMAPSS data.
Run: python predict_example.py test_FD001.txt

Alert system: Score-based, no RUL needed.
"""

import joblib
import pandas as pd
import numpy as np
import sys

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
get_alert_level = bundle['get_alert_level']

print(f"Model: Isolation Forest (contamination={bundle['config']['contamination']})")
print(f"Alert system: Score-based (🟢 OK / 🔴 ALERT)")
print()

if len(sys.argv) > 1:
    data_file = sys.argv[1]
else:
    data_file = input("Enter path to NASA test file (e.g., test_FD001.txt): ")

print(f"Loading: {data_file}")
data = pd.read_csv(data_file, sep=r'\s+', header=None, names=COLUMN_NAMES)
data = data.sort_values(['unit_id', 'cycle']).reset_index(drop=True)

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

for engine in data['unit_id'].unique():
    mask = data['unit_id'] == engine
    data.loc[mask & (data['cycle'] <= window), 'is_anomaly'] = 0

# Alert levels (NO RUL needed!)
print("Determining alert levels...")
data['alert_level'] = '🟢 OK'
for engine in data['unit_id'].unique():
    mask = data['unit_id'] == engine
    engine_data = data.loc[mask].sort_values('cycle')
    scores_history = []
    current_alert = '🟢 OK'
    for idx in engine_data.index:
        scores_history.append(data.loc[idx, 'anomaly_score'])
        current_alert = get_alert_level(scores_history.copy(), current_alert)
        data.loc[idx, 'alert_level'] = current_alert

# Results
total_anomalies = data['is_anomaly'].sum()
total_cycles    = len(data)
total_alerts    = (data['alert_level'] == '🔴 ALERT').sum()
alerted_engines = data[data['alert_level'] == '🔴 ALERT']['unit_id'].nunique()

print()
print("=" * 50)
print("RESULTS")
print("=" * 50)
print(f"Total cycles:       {total_cycles:,}")
print(f"Anomalies found:    {total_anomalies:,} ({total_anomalies/total_cycles*100:.1f}%)")
print(f"🔴 ALERT cycles:    {total_alerts:,} ({total_alerts/total_cycles*100:.1f}%)")
print(f"🔴 ALERT engines:   {alerted_engines}/{data['unit_id'].nunique()}")
print(f"Score range:        {data['anomaly_score'].min():.3f} to {data['anomaly_score'].max():.3f}")
print()
print("Sample (first 10 rows):")
print(data[['unit_id', 'cycle', 'anomaly_score', 'is_anomaly', 'alert_level']].head(10).to_string(index=False))

if alerted_engines > 0:
    print(f"\nEngines with 🔴 ALERT:")
    for eng in sorted(data[data['alert_level'] == '🔴 ALERT']['unit_id'].unique()):
        eng_data = data[(data['unit_id'] == eng) & (data['alert_level'] == '🔴 ALERT')]
        first_alert = eng_data['cycle'].min()
        print(f"  Engine #{eng}: Alert from cycle {first_alert:.0f} ({len(eng_data)} cycles)")

output_file = f'predictions_FD00{dataset_num}.csv'
data[['unit_id', 'cycle', 'anomaly_score', 'is_anomaly', 'alert_level']].to_csv(output_file, index=False)
print(f"\nResults saved to: {output_file}")