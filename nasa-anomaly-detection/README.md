## 📊 Dataset

NASA CMAPSS Turbofan Engine Degradation Simulation dataset.

| Dataset | Conditions | Fault Modes | Train Engines | Test Engines |
|---------|-----------|-------------|---------------|--------------|
| FD001 | 1 (Sea Level) | 1 (HPC) | 100 | 100 |
| FD002 | 6 (Mixed) | 1 (HPC) | 260 | 259 |
| FD003 | 1 (Sea Level) | 2 (HPC+Fan) | 100 | 100 |
| FD004 | 6 (Mixed) | 2 (HPC+Fan) | 249 | 248 |

**Total: 160,359 training rows | 709 engines | 21 sensors per cycle**

---

## 🔧 Pipeline — How the Model Was Built

### Step 1: Load Raw Data
Loaded 12 NASA files (4 train + 4 test + 4 RUL). Added 26 column names since raw files have no headers.

### Step 2: Calculate RUL (Remaining Useful Life)
Used RUL only as a training tool to identify healthy engine cycles — the model itself never sees RUL during prediction.

### Step 3: Handle Operating Conditions
- **FD001 & FD003:** 1 condition (sea level) — no special handling needed
- **FD002 & FD004:** 6 conditions (altitude, speed, throttle vary) — used KMeans clustering into 6 groups, normalized each cluster separately so normal flight changes are not flagged as anomalies

### Step 4: Rolling Features
- 21 raw sensors → 42 features (21 rolling means + 21 rolling stds)
- Window = 10 cycles
- Rolling mean captures sensor trends, rolling std captures instability

### Step 5: Normalization (StandardScaler)
Different sensors have vastly different ranges (641 vs 9000 vs 23). Scaler fitted on first 40% of engine life (healthy data only) to create a fixed healthy baseline.

### Step 6: Train Isolation Forest
- Trained on healthy data only (first 40% of engine life)
- Balanced: 6,144 rows per dataset → 24,576 total training rows
- One global model across all 4 datasets
- 100 trees, contamination = 0.05

---

## 🧪 Optimization Experiments

Professor asked us to explore improvements. Tested 9 configurations:

| Experiment | Finding |
|-----------|---------|
| No preprocessing (raw data) | ❌ Failed — 0-20% detection |
| No clustering | ❌ FD002/FD004 collapsed — 96% → 10% |
| Rolling window = 5 | ⚠️ More noise, more false positives |
| Healthy window = 45% | ❌ FD001 detection dropped significantly |
| Healthy window = 50% | ❌ FD004 false positives increased |
| Contamination = 0.05 | ✅ Sweet spot |
| Contamination = 0.07–0.15 | ⚠️ Too many false alarms |
| **40% healthy + contamination=0.05** | **🏆 WINNER** |

---

## ⚙️ Final Configuration

| Parameter | Value |
|-----------|-------|
| Algorithm | Isolation Forest |
| Number of trees | 100 |
| Healthy training window | 40% of engine life |
| Contamination | 0.05 |
| Rolling window | 10 cycles |
| Clustering | 6 clusters (FD002/FD004) |
| Scaling | StandardScaler per dataset/cluster |
| Training samples | 24,576 (6,144 × 4 datasets) |

---

## 🔄 Update — Score-Based Alert System (01.06.2026)

### What Changed

The original model used **RUL (Remaining Useful Life)** to determine engine health status. This was problematic because:

- RUL is only available in historical NASA data — not on live engines
- Health zones (Healthy/Warning/Critical) depended on knowing exactly when the engine would fail
- The model couldn't be deployed in production where true RUL is unknown

### The Fix

Replaced RUL-based health zones with a **score-based alert system** that uses only anomaly scores:

| Before (RUL-Based) | After (Score-Based) |
|---------------------|---------------------|
| 🟢 Healthy (RUL > 50) | 🟢 OK |
| 🟠 Warning (RUL 30-50) | 🔴 ALERT |
| 🔴 Critical (RUL ≤ 30) | |

### How the Alert System Works

The `get_alert_level()` function analyzes anomaly score history using 4 signals:

1. **Current level** — Rolling average of last 10 scores
2. **Rate of change** — Is the score deteriorating?
3. **Personal baseline** — Is this worse than the engine's own healthy state?
4. **Persistence** — How many consecutive negative scores?

**Alert triggers:** 8 bad cycles out of last 20 → 🔴 ALERT
**Alert clears:** 15 good cycles out of last 20 → 🟢 OK
**Warmup protection:** First 10 cycles always 🟢 OK
**Stability:** Average 0.1–0.6 transitions per engine (no flickering)

### Why Two Levels Instead of Three?

Analysis showed that anomaly scores don't separate cleanly into three groups (Healthy/Warning/Critical). The "Warning" zone was mostly noise — scores hovering near zero. Simplifying to two levels makes the system clearer and more reliable.

### Updated Model Bundle

The file `anomaly_detection_model.joblib` now includes:

| Item | Description |
|------|-------------|
| `model` | Trained Isolation Forest (unchanged) |
| `scalers` | StandardScaler per dataset (unchanged) |
| `cluster_models` | KMeans for FD002/FD004 (unchanged) |
| `feature_cols` | 42 feature names (unchanged) |
| `get_alert_level` | **NEW** — Score-based alert function |

The training pipeline and model weights are identical to the original — only the output layer (health determination) was updated.

---

## 🚨 Alert System Performance

### Alert Stability by Dataset

| Dataset | Avg Transitions | Max Transitions | 0 Transitions | ≤2 Transitions |
|---------|----------------|-----------------|---------------|----------------|
| FD001 | 0.1 | 1 | 92% | 100% |
| FD002 | 0.3 | 3 | 71% | 99% |
| FD003 | 0.4 | 4 | 74% | 95% |
| FD004 | 0.6 | 6 | 63% | 96% |

### Alert Detection by Dataset

| Dataset | Engines Alerted | False Alerts (First 30% Life) | True False Rate* |
|---------|----------------|------------------------------|------------------|
| FD001 | 8% | 0.0% | 0.0% |
| FD002 | 29% | 2.3% | ~1% |
| FD003 | 26% | 10.0% | ~4% |
| FD004 | 37% | 8.9% | ~5% |

*\*60% of "false alerts" on FD003/FD004 are actually early warnings — the engine degrades later in life. True false alarm rate is ~4-5%.*

---

## 📈 Original Model Performance

### Training Data (160,359 cycles)

| Dataset | Critical Detection | Healthy False Alarms | Status |
|---------|-------------------|---------------------|--------|
| FD001 | 78.9% | 0.2% | ✅ |
| FD002 | 94.4% | 4.5% | ✅ |
| FD003 | 86.2% | 7.0% | ✅ |
| FD004 | 96.9% | 10.5% | ⚠️ |

### Test Data — Unseen Engines (104,897 cycles)

| Dataset | Critical Detection | Healthy False Alarms | Status |
|---------|-------------------|---------------------|--------|
| FD001 | 58.4% | 0.3% | ✅ |
| FD002 | 92.4% | 3.7% | ✅ |
| FD003 | 85.6% | 6.2% | ✅ |
| FD004 | 90.5% | 8.6% | ✅ |

**7/8 validations passed** (Critical >50%, Healthy <10%)

### Improvement Over Original Baseline

| Metric | Before | After |
|--------|--------|-------|
| FD003 Critical Detection | 73.2% | **85.6%** (+12.4%) |
| FD002 Healthy False Alarms | 6.4% | **3.7%** (−42%) |

---

## 🚀 How to Use the Model

### Quick Start (Easiest Way)

Use the included demo script. It handles everything automatically and works on all 4 datasets:

```bash
# Install requirements
pip install joblib numpy pandas scikit-learn

# Run on any NASA test file
python predict_example.py test_FD001.txt
The script automatically detects which dataset you're using and applies the correct preprocessing (clustering for FD002/FD004, single scaling for FD001/FD003). Results are printed to the screen and saved as a CSV file.


```
### Manual Usage (Advanced)

If you want to integrate the model into your own code:

```bash


import joblib
import pandas as pd
import numpy as np

# Load model bundle
bundle = joblib.load('anomaly_detection_model.joblib')
model = bundle['model']
scalers = bundle['scalers']
cluster_models = bundle['cluster_models']
feature_cols = bundle['feature_cols']
sensor_cols = bundle['sensor_cols']
window = bundle['rolling_window']
get_alert_level = bundle['get_alert_level']

# Load your data
COLUMN_NAMES = ['unit_id', 'cycle', 'op_setting_1', 'op_setting_2', 'op_setting_3',
    'sensor_1', 'sensor_2', 'sensor_3', 'sensor_4', 'sensor_5',
    'sensor_6', 'sensor_7', 'sensor_8', 'sensor_9', 'sensor_10',
    'sensor_11', 'sensor_12', 'sensor_13', 'sensor_14', 'sensor_15',
    'sensor_16', 'sensor_17', 'sensor_18', 'sensor_19', 'sensor_20', 'sensor_21']

data = pd.read_csv('test_FD001.txt', sep='\s+', header=None, names=COLUMN_NAMES)
data = data.sort_values(['unit_id', 'cycle']).reset_index(drop=True)

# Preprocess (FD001 example — see predict_example.py for FD002/FD004)
data[sensor_cols] = scalers[1].transform(data[sensor_cols].astype(float))

for engine in data['unit_id'].unique():
    mask = data['unit_id'] == engine
    for sensor in sensor_cols:
        data.loc[mask, f'{sensor}_roll_mean'] = data.loc[mask, sensor].rolling(window=window, min_periods=1).mean().values
        data.loc[mask, f'{sensor}_roll_std'] = data.loc[mask, sensor].rolling(window=window, min_periods=1).std().values

# Predict anomalies
data['anomaly_score'] = model.decision_function(data[feature_cols])
data['is_anomaly'] = (model.predict(data[feature_cols]) == -1).astype(int)

# Fix warmup cycles
for engine in data['unit_id'].unique():
    mask = data['unit_id'] == engine
    data.loc[mask & (data['cycle'] <= window), 'is_anomaly'] = 0

# Get alert levels (NO RUL needed!)
scores_history = []
alerts = []
current = '🟢 OK'
for score in data['anomaly_score']:
    scores_history.append(score)
    current = get_alert_level(scores_history.copy(), current)
    alerts.append(current)
data['alert_level'] = alerts

print(f"Anomalies: {data['is_anomaly'].sum()} / {len(data)}")
print(f"Alerts: {(data['alert_level'] == '🔴 ALERT').sum()} cycles")
```

---

### 📋 CSV Output Columns

| Column | Description |
|-----------|-------|
| unit_id | Engine number |
| cycle | Operating cycle number |
| anomaly_score | Continuous score (more negative = more anomalous) |
| is_anomaly | 1 = anomaly detected, 0 = normal |
| alert_level | 🟢 OK or 🔴 ALERT (score-based, no RUL needed) |

---

### 📋 Key Design Decisions

| Decision | Why |
|-----------|-------|
| Score-based alerts, not RUL-based | Works on live engines where true RUL is unknown |
| Two alert levels (not three) | Scores don't separate into three clean groups — simpler is clearer |
| Alert persistence (hysteresis) | Prevents flickering — 0.1-0.6 transitions per engine |
| Engineer as final decision-maker | Model screens, human decides — 60% of early alerts are genuine early warnings |
| Train on healthy data only | Model learns "normal" — anything different is flagged |

---

### ⚠️ Limitations

- Sensors change only 0.3-1.8% from healthy to failing — degradation signal is physically subtle

- FD003/FD004 show ~9-10% alert rate on early healthy data — but 60% of these are early detection, not false alarms

- Requires the exact same preprocessing pipeline as training

- Only tested on NASA CMAPSS data 2008

- Model is a screening tool — engineer must review alerts before taking action

