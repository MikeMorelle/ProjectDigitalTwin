import joblib
import pandas as pd
from ml.features.feature_prep import add_rolling_features

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

cols = ["engine_id", "cycle", "op1", "op2", "op3"] + [f"s{i}" for i in range(1, 22)]
df = pd.read_csv("data/train_FD001.txt", sep=r"\s+", header=None)
df.columns = cols

X = add_rolling_features(df)
feature_cols = X.columns.tolist()

#enough for FD001 & 003, but 002 & 004 need condition clustering
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = IsolationForest(
    n_estimators=200,
    contamination=0.01,
    random_state=42,
    n_jobs=-1
)

model.fit(X_scaled)

joblib.dump(model, "iforest.pkl")
joblib.dump(feature_cols, "feature_cols.pkl")
joblib.dump(scaler, "scaler.pkl")