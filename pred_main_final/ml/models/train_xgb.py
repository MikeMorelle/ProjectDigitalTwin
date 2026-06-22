import pandas as pd

SENSORS = [f"sensor_{i}" for i in range(1, 22)]
FEATURES = ["op1", "op2", "op3"] + SENSORS
col_names = ["engine_id", "cycle"] + FEATURES

train = pd.read_csv('train_FD001.txt', sep=r'\s+', header=None, names=col_names)


max_cycles = train.groupby("engine_id")["cycle"].max()

train["RUL"] = train.apply(lambda row: max_cycles[row["engine_id"]] - row["cycle"],axis=1)

test = pd.read_csv('test_FD001.txt', sep=r'\s+', header=None, names=col_names)
y_test = pd.read_csv('RUL_FD001.txt', sep=r'\s+', header=None, names=["RUL"])
window=10

for sensor in col_names:

    if sensor == "RUL" or sensor=="engine_id" or sensor=="cycle" or sensor =="op1" or sensor =="op2" or sensor =="op3":
        continue

    test[f"{sensor}_roll_mean"] = (
        test.groupby("engine_id")[sensor]
        .transform(
            lambda x: x.rolling(window, min_periods=1).mean()
        )
    )

    test[f"{sensor}_roll_std"] = (
        test.groupby("engine_id")[sensor]
        .transform(
            lambda x: x.rolling(window, min_periods=2).std()
        )
    )

    train[f"{sensor}_roll_mean"] = (
        train.groupby("engine_id")[sensor]
        .transform(
            lambda x: x.rolling(window, min_periods=1).mean()
        )
    )

    train[f"{sensor}_roll_std"] = (
        train.groupby("engine_id")[sensor]
        .transform(
            lambda x: x.rolling(window, min_periods=2).std()
        )
    )

exclude_cols = col_names

feature_cols = [
    col for col in test.columns
    if col not in exclude_cols
]

X_train = train[feature_cols]
test_last = test.groupby("engine_id").last().reset_index()
X_test = test_last[feature_cols]

X_train = X_train.fillna(0)
X_test = X_test.fillna(0)

y_train = train["RUL"]

test_last = test.groupby("engine_id").last().reset_index()

y_test = y_test.iloc[:,0]


y_train = y_train.clip(upper=125)
y_test = y_test.clip(upper=125)

print(f"Y_TRAIN: {y_train.shape} | X_TRAIN: {X_train.shape} | Y_TEST:  {y_test.shape} | X_TEST: {X_test.shape}")

from xgboost import XGBRegressor

rul_model = XGBRegressor(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="reg:squarederror",
    random_state=42
)

rul_model.fit(X_train, y_train)

import joblib

bundle = {
    "rul_model": rul_model,
    "feature_cols": feature_cols
}

joblib.dump(bundle, "rul_model.joblib")