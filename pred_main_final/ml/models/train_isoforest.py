# ============================================================
# train_model.py
# This file trains the anomaly detection model from scratch.
# Just run it, and it creates the model file at the end.
# ============================================================

# Step 1: Import the tools we need
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import joblib

# ----------------------------------------------------------
# The column names for the NASA data files.
# The raw files have no column names, so we give them names.
# There are 26 columns in total.
# ----------------------------------------------------------
COLUMN_NAMES = [
    "unit_id", "cycle", "op_setting_1", "op_setting_2", "op_setting_3",
    "sensor_1", "sensor_2", "sensor_3", "sensor_4", "sensor_5",
    "sensor_6", "sensor_7", "sensor_8", "sensor_9", "sensor_10",
    "sensor_11", "sensor_12", "sensor_13", "sensor_14", "sensor_15",
    "sensor_16", "sensor_17", "sensor_18", "sensor_19", "sensor_20", "sensor_21"
]

# These are the 21 sensor columns we actually use (ignoring op settings)
SENSOR_COLS = []
for i in range(1, 22):
    SENSOR_COLS.append(f"sensor_{i}")

# ----------------------------------------------------------
# Settings that gave the best results after testing
# ----------------------------------------------------------
HEALTHY_PERCENT = 0.40   # Use first 40% of engine life for training
ROLLING_WINDOW = 10      # Average 10 cycles together
CONTAMINATION  = 0.05    # Expect 5% of data to be anomalous

# ----------------------------------------------------------
# Helper functions
# ----------------------------------------------------------

def load_one_file(file_number, folder_path):
    """
    Load one NASA data file.
    file_number: 1, 2, 3, or 4
    Returns a DataFrame (table) with column names added.
    """
    file_path = folder_path + f"train_FD00{file_number}.txt"
    # The file has columns separated by spaces, and no header row
    df = pd.read_csv(file_path, sep=r"\s+", header=None, names=COLUMN_NAMES)
    # Sort by engine ID first, then by cycle number
    df = df.sort_values(["unit_id", "cycle"])
    df = df.reset_index(drop=True)  # Reset row numbers after sorting
    return df


def add_rul_column(df):
    """
    Add a column called 'RUL' (Remaining Useful Life).
    RUL = how many cycles until this engine fails.
    Example: If engine 1's last cycle is 200, then at cycle 50 the RUL is 150.
    """
    df = df.copy()
    # Find the last cycle for each engine
    max_cycles = df.groupby("unit_id")["cycle"].max()
    # Subtract the current cycle from the max cycle
    df["RUL"] = df["unit_id"].map(max_cycles) - df["cycle"]
    return df


def compute_rolling_features(df, window=10):
    """
    For each sensor, create two new columns:
    - sensor_X_roll_mean: average of the last 'window' cycles
    - sensor_X_roll_std:  standard deviation of the last 'window' cycles
    
    This turns 21 sensors into 42 features (21 means + 21 stds).
    Each engine is processed separately so they don't mix.
    """
    df = df.copy()
    
    # Get a list of all engine IDs
    all_engines = df["unit_id"].unique()
    
    for engine_id in all_engines:
        # Find rows that belong to this engine
        engine_rows = df["unit_id"] == engine_id
        
        for sensor_name in SENSOR_COLS:
            # Rolling mean
            df.loc[engine_rows, f"{sensor_name}_roll_mean"] = (
                df.loc[engine_rows, sensor_name]
                .rolling(window=window, min_periods=1)
                .mean()
                .values
            )
            # Rolling standard deviation
            df.loc[engine_rows, f"{sensor_name}_roll_std"] = (
                df.loc[engine_rows, sensor_name]
                .rolling(window=window, min_periods=1)
                .std()
                .values
            )
    
    return df


def get_feature_columns():
    """
    Build the list of 42 feature column names.
    Example: sensor_1_roll_mean, sensor_1_roll_std, sensor_2_roll_mean, ...
    """
    feature_list = []
    for sensor_name in SENSOR_COLS:
        feature_list.append(f"{sensor_name}_roll_mean")
        feature_list.append(f"{sensor_name}_roll_std")
    return feature_list


# ============================================================
# START OF THE MAIN PIPELINE
# ============================================================

print("Step 1: Loading the four training datasets...")
print("-" * 40)

# Change this to where your NASA files are
DATA_FOLDER = "data/"

# We'll store the four datasets in a dictionary
train_data = {}

for i in [1, 2, 3, 4]:
    # Load the file
    df = load_one_file(i, DATA_FOLDER)
    # Add the RUL column
    df = add_rul_column(df)
    # Save it
    train_data[i] = df
    
    # Print how much data we loaded
    num_rows = len(df)
    num_engines = df["unit_id"].nunique()
    print(f"  FD00{i}: {num_rows:,} rows, {num_engines} engines")

# ----------------------------------------------------------
print("\nStep 2: Clustering and normalization...")
print("-" * 40)

# We'll store our scalers and cluster models here
all_scalers = {}
all_cluster_models = {}

for dataset_num in [1, 2, 3, 4]:
    df = train_data[dataset_num].copy()
    
    if dataset_num in [2, 4]:
        # These datasets have 6 different operating conditions
        # We need to group flights first, then normalize each group
        
        # Use KMeans to find 6 clusters based on operating settings
        op_settings = df[["op_setting_1", "op_setting_2", "op_setting_3"]]
        kmeans = KMeans(n_clusters=6, random_state=42, n_init=10)
        df["cluster"] = kmeans.fit_predict(op_settings)
        all_cluster_models[dataset_num] = kmeans
        
        # Normalize each cluster separately
        cluster_scalers = {}
        for cluster_id in range(6):
            rows_in_cluster = df["cluster"] == cluster_id
            if rows_in_cluster.sum() > 0:
                scaler = StandardScaler()
                # Fit on the data in this cluster, then transform
                df.loc[rows_in_cluster, SENSOR_COLS] = scaler.fit_transform(
                    df.loc[rows_in_cluster, SENSOR_COLS].astype(float)
                )
                cluster_scalers[cluster_id] = scaler
        
        all_scalers[dataset_num] = cluster_scalers
        
        # Show cluster sizes
        cluster_counts = df["cluster"].value_counts().sort_index()
        print(f"  FD00{dataset_num}: 6 clusters, sizes: {dict(cluster_counts)}")
        
    else:
        # These datasets have only 1 operating condition (sea level)
        # We can just normalize all sensors together
        
        # But we fit the scaler only on the first 40% of each engine's life
        # (the healthiest part)
        num_engines = df["unit_id"].nunique()
        healthy_count = int(num_engines * HEALTHY_PERCENT)
        healthy_engine_ids = df["unit_id"].unique()[:healthy_count]
        healthy_rows = df["unit_id"].isin(healthy_engine_ids)
        
        scaler = StandardScaler()
        scaler.fit(df.loc[healthy_rows, SENSOR_COLS].astype(float))
        df[SENSOR_COLS] = scaler.transform(df[SENSOR_COLS].astype(float))
        all_scalers[dataset_num] = scaler
        
        print(f"  FD00{dataset_num}: 1 condition, scaler fitted on {healthy_count} engines")
    
    # Save the processed data
    train_data[dataset_num] = df

# ----------------------------------------------------------
print("\nStep 3: Computing rolling features...")
print("-" * 40)

for dataset_num in [1, 2, 3, 4]:
    train_data[dataset_num] = compute_rolling_features(
        train_data[dataset_num],
        window=ROLLING_WINDOW
    )

FEATURE_COLS = get_feature_columns()
print(f"  Created {len(FEATURE_COLS)} features (21 sensors × 2)")

# ----------------------------------------------------------
print("\nStep 4: Preparing healthy training data...")
print("-" * 40)

all_training_parts = []

for dataset_num in [1, 2, 3, 4]:
    df = train_data[dataset_num]
    
    # Find the healthy part of each engine's life (first 40%)
    # Healthy = RUL > 60% of the engine's total life
    max_rul_per_engine = df.groupby("unit_id")["RUL"].transform("max")
    healthy_mask = df["RUL"] > max_rul_per_engine * (1 - HEALTHY_PERCENT)
    healthy_data = df[healthy_mask]
    
    # Take a balanced sample: same number of rows from each dataset
    sample_size = min(6144, len(healthy_data))
    sampled_data = healthy_data.sample(n=sample_size, random_state=42)
    
    all_training_parts.append(sampled_data[FEATURE_COLS])
    print(f"  FD00{dataset_num}: {len(healthy_data):,} healthy rows → sampled {sample_size:,}")

# Combine all four datasets into one big training set
X_train = pd.concat(all_training_parts, axis=0)
print(f"  Total training data: {X_train.shape[0]:,} rows × {X_train.shape[1]} features")

# ----------------------------------------------------------
print("\nStep 5: Training the Isolation Forest...")
print("-" * 40)

model = IsolationForest(
    n_estimators=100,
    contamination=CONTAMINATION,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train)
print("  Model training complete!")

# ----------------------------------------------------------
print("\nStep 6: Adding the alert function...")
print("-" * 40)

# This function decides if an engine is OK or needs attention.
# It uses only the anomaly scores (no RUL needed).
def get_alert_level(scores_history, current_alert="OK"):
    """
    Decide the alert level based on recent anomaly scores.
    scores_history: a list of anomaly scores (newest at the end)
    current_alert: what the alert is right now ("OK" or "ALERT")
    Returns: "OK" or "ALERT"
    """
    # Need at least 10 cycles before we can judge
    if len(scores_history) <= 10:
        return "OK"
    
    scores = np.array(scores_history)
    bad_count = 0
    good_count = 0
    
    # Look at the last 5 cycles
    for i in range(len(scores) - 5, len(scores)):
        # Average of the last 10 cycles ending at this point
        avg_of_last_10 = np.mean(scores[i-9:i+1])
        
        # Count how many consecutive negative scores we have
        consecutive_negatives = 0
        for j in range(i, -1, -1):
            if scores[j] < 0:
                consecutive_negatives += 1
            else:
                break
        
        # A cycle is "bad" if:
        # - The 10-cycle average is negative, OR
        # - We have 3+ consecutive negative scores, OR
        # - This cycle's score is below -0.003
        is_bad = (
            avg_of_last_10 < 0.0 or
            consecutive_negatives >= 3 or
            scores[i] < -0.003
        )
        
        if is_bad:
            bad_count += 1
        else:
            good_count += 1
    
    # Decision rules
    if current_alert == "OK":
        # Need 5 bad cycles in the last 5 to trigger an alert
        if bad_count >= 5:
            return "ALERT"
        else:
            return "OK"
    
    elif current_alert == "ALERT":
        # Need 3 good cycles in the last 5 to clear the alert
        if good_count >= 3:
            return "OK"
        else:
            return "ALERT"
    
    return "OK"


print("  Alert function defined!")

# ----------------------------------------------------------
print("\nStep 7: Saving the model bundle...")
print("-" * 40)

# Put everything in one dictionary (the "bundle")
bundle = {
    "model": model,                       # The trained Isolation Forest
    "scalers": all_scalers,               # StandardScaler objects
    "cluster_models": all_cluster_models, # KMeans objects for FD002/FD004
    "feature_cols": FEATURE_COLS,         # List of 42 feature column names
    "sensor_cols": SENSOR_COLS,           # List of 21 sensor column names
    "rolling_window": ROLLING_WINDOW,     # The window size (10)
    "get_alert_level": get_alert_level,   # The alert function
    "config": {                           # Training settings
        "healthy_pct": HEALTHY_PERCENT,
        "contamination": CONTAMINATION,
        "model_type": "IsolationForest",
        "n_estimators": 100
    }
}

# Save to a file
joblib.dump(bundle, "anomaly_detection_model.joblib")
print("  Saved: anomaly_detection_model.joblib")

print("\n" + "=" * 50)
print("  DONE! Model is trained and saved.")
print("=" * 50)