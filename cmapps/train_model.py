import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from xgboost import XGBRegressor
import joblib
from components import read_data, prep_data

train, test, y_test = read_data.prepare_all()

train = prep_data.add_remaining_useful_life(train)
print("FEATURES OF TRAIN: \n",train.columns, "\n")

#currently hard coded important feat selection (better results)
del_cols = ["setting1", "setting2", "setting3","sensor1", "sensor5", "sensor6", "sensor10", "sensor14", "sensor16", "sensor18", "sensor19"]
train = train.drop(del_cols, axis=1)
test = test.drop(del_cols, axis=1)

#automatic filter as alternative
#low_var_cols = [c for c in train.columns if train[c].std() < 1e-3]
print("AFTER FEATURE SELECTION: \n", train.columns, "\n")

#split into train and test and save feat cols for ui
X_train, y_train, X_test, y_test = prep_data.split_data(train, test, y_test)
feature_cols = X_train.columns
print("COLUMNS OF X_TRAIN: \n", X_train.columns, "\n Y_TRAIN: \n", y_train.name, "\n X_TEST: \n", X_test.columns, "\n Y_TEST: \n", y_test.name, "\n")

#clip for better performance, as machines degrade after time t, not from beginning -> tested by plotting
y_train = y_train.clip(upper=125)
y_test = y_test.clip(upper=125)

#fit scaler with train and scale both data sets
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

#simple gradient boost reg
model = XGBRegressor()
model.fit(X_train_scaled, y_train)
preds = model.predict(X_test_scaled)

#eval matrix
mse = np.sqrt(mean_squared_error(y_test,preds))
mae = mean_absolute_error(y_test,preds)
r2 = r2_score(y_test,preds)
print(f"MSE: {mse:.2f}")
print(f"MAE: {mae:.2f}")
print(f"r2: {r2:.2f}")
feature_cols = X_train.columns.tolist()

#save model, scaler and feat names for later use
joblib.dump(model, "models/xgb_rul_model.pkl")
joblib.dump(scaler, "models/scaler.pkl")
joblib.dump(feature_cols, "models/features.pkl")
print("Model saved.")