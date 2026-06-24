import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from keras.callbacks import EarlyStopping, ReduceLROnPlateau
import keras
from keras import layers

columns = ['engine_id', 'cycle', 'op1', 'op2', 'op3'] + \
          [f'sensor_{i}' for i in range(1, 22)]

train = pd.read_csv('train_FD001.txt', sep=r'\s+', header=None, names=columns)
test = pd.read_csv( 'test_FD001.txt', sep=r'\s+', header=None, names=columns)
rul_test = pd.read_csv('RUL_FD001.txt', sep=r'\s+', header=None, names=['RUL'])

train['RUL'] = train.groupby('engine_id')['cycle'].transform(lambda x: x.max() - x)


#if not drop constants
feature_cols = [
    col for col in columns
]

scaler = MinMaxScaler()
train[feature_cols] = scaler.fit_transform(train[feature_cols])
test[feature_cols] = scaler.transform(test[feature_cols])

SEQUENCE_LENGTH = 30

def create_sequences(df, seq_len):
    X, y = [], []

    for engine_id, group in df.groupby("engine_id"):
        group = group.sort_values("cycle")

        values = group[feature_cols].values
        rul = group["RUL"].values

        for i in range(len(values) - seq_len + 1):
            X.append(values[i:i+seq_len])
            y.append(rul[i+seq_len-1])

    return np.array(X), np.array(y)

X_train, y_train = create_sequences(train, SEQUENCE_LENGTH)

def create_test_sequences(df, seq_len, feature_cols):
    X_test = []
    y_test = []

    # RUL mapping ist wichtig (CMAPSS korrekt)
    # Annahme: rul_test ist in engine order
    rul_values = rul_test["RUL"].values

    for idx, (engine_id, group) in enumerate(df.groupby("engine_id")):

        group = group.sort_values("cycle")

        values = group[feature_cols].values

        # Padding falls zu kurz
        if len(values) < seq_len:
            pad = np.zeros((seq_len - len(values), len(feature_cols)))
            values = np.vstack([pad, values])

        # letzte Sequenz nehmen
        X_test.append(values[-seq_len:])

        # CMAPSS: rul_test ist in gleicher Reihenfolge wie sorted engines
        y_test.append(rul_values[idx])

    return np.array(X_test), np.array(y_test)
  
X_test, y_test = create_test_sequences(test, SEQUENCE_LENGTH, columns)

model = keras.Sequential([
    layers.Input(shape=(SEQUENCE_LENGTH, len(feature_cols))),

    layers.LSTM(64, return_sequences=True),
    layers.Dropout(0.3),

    layers.LSTM(32, return_sequences=False),
    layers.Dropout(0.3),

    layers.Dense(32, activation='relu'),
    layers.Dense(1)
])

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-3),
    loss='mse',
    metrics=['mae']
)


callbacks = [
    EarlyStopping(
        monitor="val_loss",
        patience=8,
        restore_best_weights=True
    ),
    ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=3
    )
]

history = model.fit(
    X_train, y_train,
    validation_split=0.2,
    epochs=50,
    batch_size=128,
    callbacks=callbacks,
    verbose=1
)

from sklearn.metrics import mean_absolute_error

pred = model.predict(X_test)

print("MAE:", mean_absolute_error(y_test, pred))
#got around 17.9 as MAE

model.save("lstm_rul.keras")

import joblib

joblib.dump({
    "scaler": scaler,
    "feature_cols": feature_cols,
    "seq_len": SEQUENCE_LENGTH
}, "lstm_meta.joblib")