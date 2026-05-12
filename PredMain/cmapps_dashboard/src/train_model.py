import pandas as pd
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
import joblib
from feature_engineering import build_window_features, WINDOW


#load data
index_names = ['unit_num', 'time_cycles']
setting_names = ['setting1', 'setting2', 'setting3']
sensor_names = ['sensor{}'.format(i) for i in range(1, 22)]
col_names = index_names + setting_names + sensor_names
train = pd.read_csv("cmapps_dashboard/data/train_FD001.txt", sep='\s+', header=None, names=col_names)
test = pd.read_csv("cmapps_dashboard/data/test_FD001.txt", sep='\s+', header=None, names=col_names)
y_test = pd.read_csv("cmapps_dashboard/data/RUL_FD001.txt", sep='\s+', header=None, names=['RUL'])


def add_remaining_useful_life(df):
    """Calculate the Remaining Useful Life (RUL) for each engine in the dataset. 
    RUL is calculated as the difference between the maximum number of cycles for each engine and the current cycle."""

    #Calculate the total number of cycles for each engine
    n_cycles = df.groupby("unit_num")["time_cycles"].max()

    #Create a copy of the DataFrame to avoid modifying the original
    df = df.copy()

    #Merge the max number of cycles back into the original DataFrame
    df = df.merge(
        n_cycles.rename("n_cycles"),
        left_on="unit_num",
        right_index=True
    )

    #Calculate RUL as the difference between the max cycles and the current cycle
    df["RUL"] = df["n_cycles"] - df["time_cycles"]

    #Drop the n_cycles column as it's no longer needed
    df = df.drop("n_cycles", axis=1)

    return df

train = add_remaining_useful_life(train)

#Drop unneeded columns to simplify the dataset (currently hardcoded...future auto feature selection would be better)
del_cols = ["setting1", "setting2", "setting3","sensor1", "sensor5", "sensor6", "sensor10", "sensor14", "sensor16", "sensor18", "sensor19"]
train = train.drop(del_cols, axis=1)
test = test.drop(del_cols, axis=1)

#store rolling features for each engine in a list 
feature_rows = []

#Iterate through each engine and build features using a rolling window of sensor data
for eng_id in train["unit_num"].unique():

    #Extract the data for the current engine
    eng = train[train["unit_num"] == eng_id]

    #Simulate real-time data processing by iterating through the sensor data with a rolling window
    for i in range(WINDOW, len(eng)):

        #Extract the current window of sensor data and build features
        window = eng.iloc[i-WINDOW:i]
        row = build_window_features(window)

        #Add the RUL for the current cycle to the feature row
        row["RUL"] = eng.iloc[i]["RUL"]

        feature_rows.append(row)

#Create a DataFrame from the list of feature rows
feat_df = pd.DataFrame(feature_rows)

#Split the data into features and target variable
X_train = train.drop(
    ["unit_num","time_cycles", "RUL"],
    axis=1
    )
y_train = train["RUL"]

#For the test set, we only want to predict the RUL for the last cycle of each engine, so we take the last row for each engine
test_last = test.groupby("unit_num").last().reset_index()
X_test = test_last.drop(
    ["unit_num", "time_cycles"],
    axis=1
)
y_test = y_test.iloc[:,0]

#Clip the RUL values to a maximum of 125 to prevent extreme values from skewing the model
y_train = y_train.clip(upper=125)
y_test = y_test.clip(upper=125)

#XGBoost model as an example - can be replaced with any regression model
model = XGBRegressor(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.03,
    subsample=0.8,
    random_state=42
)

model.fit(X_train, y_train)

feat_cols = X_train.columns

#Save the trained model and feature columns for later use in the real-time prediction script
joblib.dump(model, "cmapps_dashboard/models/rul_model.pkl")
joblib.dump(feat_cols, "cmapps_dashboard/models/feat_cols.pkl")

print("Model gespeichert")