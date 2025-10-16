# train_lstm.py
import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# parámetros
CSV_PATH = "ocupacion_5min.csv"
MODEL_PATH = "lstm_model_v1.h5"
SCALER_PATH = "scaler_y_v1.pkl"

# serie: cada paso = 5 minutos
STEP_MINUTES = 5
H_minutes = 40
H = H_minutes // STEP_MINUTES  # 8
T_past = 24  # ventanas pasadas: 24*5min = 120min (2h)

def load_data(csv_path):
    df = pd.read_csv(csv_path, parse_dates=['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    # Asegurar columna 'ocupados'
    if 'ocupados' not in df.columns:
        raise ValueError("CSV debe contener columna 'ocupados'")
    return df[['timestamp','ocupados']]

def make_supervised(series, T_past, H):
    X, y = [], []
    vals = series.values.astype('float32')
    n = len(vals)
    for i in range(n - T_past - H + 1):
        X.append(vals[i: i + T_past])
        y.append(vals[i + T_past: i + T_past + H])
    if not X:
        return np.empty((0, T_past)), np.empty((0, H))
    return np.array(X), np.array(y)

def train():
    df = load_data(CSV_PATH)
    # Si hay muy pocos datos, avisar
    if len(df) < (T_past + H + 1):
        print("ATENCIÓN: muy pocos datos para entrenar LSTM. Filas:", len(df))
        # no abortar: igual intentamos un run rápido
    series = df['ocupados']

    # escalado (escalamos la serie completa por simplicidad)
    scaler_y = MinMaxScaler(feature_range=(0,1))
    vals = series.values.reshape(-1,1)
    vals_scaled = scaler_y.fit_transform(vals).flatten()

    X, y = make_supervised(pd.Series(vals_scaled), T_past, H)
    if X.shape[0] == 0:
        print("No hay ventanas suficientes. Generando ejemplo para continuar (no recomendado).")
        return

    # reshape X -> (samples, T_past, 1)
    X = X.reshape((X.shape[0], X.shape[1], 1))
    y = y.reshape((y.shape[0], y.shape[1]))  # salida multi-step

    # split train/val
    split = int(0.8 * len(X))
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]

    # construir modelo
    n_features = 1
    model = Sequential([
        LSTM(64, input_shape=(T_past, n_features), return_sequences=False),
        Dropout(0.2),
        Dense(32, activation='relu'),
        Dense(H, activation='linear')
    ])
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])

    callbacks = [
        EarlyStopping(monitor='val_loss', patience=6, restore_best_weights=True),
        ModelCheckpoint(MODEL_PATH + ".tmp", save_best_only=True, monitor='val_loss')
    ]

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=60,
        batch_size=32,
        callbacks=callbacks,
        verbose=2
    )

    # guardar modelo final
    model.save(MODEL_PATH)
    joblib.dump(scaler_y, SCALER_PATH)
    print("Modelo guardado en:", MODEL_PATH)
    print("Scaler guardado en:", SCALER_PATH)

if __name__ == "__main__":
    train()
