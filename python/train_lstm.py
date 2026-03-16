# train_lstm.py
import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.neural_network import MLPRegressor
import joblib
TF_AVAILABLE = True
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
except Exception:
    TF_AVAILABLE = False

# parámetros
CSV_PATH = "ocupacion_5min.csv"
MODEL_PATH = "lstm_model_v1.h5"
SCALER_X_PATH = "scaler_x_v1.pkl"
SCALER_PATH = "scaler_y_v1.pkl"
FALLBACK_MODEL_PATH = "lstm_model_fallback.pkl"

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
    if 'hora' not in df.columns:
        df['hora'] = df['timestamp'].dt.hour
    if 'dia_semana' not in df.columns:
        df['dia_semana'] = df['timestamp'].dt.dayofweek
    if 'registrado_ratio' not in df.columns:
        df['registrado_ratio'] = 0.9

    cols = ['timestamp', 'ocupados', 'hora', 'dia_semana', 'registrado_ratio']
    return df[cols]

def make_supervised(features_scaled, target_scaled, T_past, H):
    X, y = [], []
    n = len(features_scaled)
    for i in range(n - T_past - H + 1):
        X.append(features_scaled[i: i + T_past])
        y.append(target_scaled[i + T_past: i + T_past + H])
    if not X:
        return np.empty((0, T_past, 1)), np.empty((0, H))
    return np.array(X), np.array(y)

def train():
    df = load_data(CSV_PATH)
    # Si hay muy pocos datos, avisar
    if len(df) < (T_past + H + 1):
        print("ATENCIÓN: muy pocos datos para entrenar LSTM. Filas:", len(df))
        # no abortar: igual intentamos un run rápido
    
    features = df[['ocupados', 'hora', 'dia_semana', 'registrado_ratio']].astype('float32')
    target = df['ocupados'].astype('float32').values.reshape(-1, 1)

    scaler_x = MinMaxScaler(feature_range=(0,1))
    scaler_y = MinMaxScaler(feature_range=(0,1))
    features_scaled = scaler_x.fit_transform(features)
    target_scaled = scaler_y.fit_transform(target).flatten()

    X, y = make_supervised(features_scaled, target_scaled, T_past, H)
    if X.shape[0] == 0:
        print("No hay ventanas suficientes. Generando ejemplo para continuar (no recomendado).")
        return

    y = y.reshape((y.shape[0], y.shape[1]))  # salida multi-step

    # split train/val
    split = int(0.8 * len(X))
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]

    if TF_AVAILABLE:
        n_features = X.shape[2]
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

        model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=60,
            batch_size=32,
            callbacks=callbacks,
            verbose=2
        )
        model.save(MODEL_PATH)
        print("Modelo LSTM guardado en:", MODEL_PATH)
    else:
        print("TensorFlow no disponible. Entrenando modelo secuencial de respaldo para demo.")
        x_train_flat = X_train.reshape((X_train.shape[0], -1))
        x_val_flat = X_val.reshape((X_val.shape[0], -1))
        model = MLPRegressor(
            hidden_layer_sizes=(128, 64),
            activation='relu',
            solver='adam',
            random_state=42,
            max_iter=80,
            early_stopping=True,
            validation_fraction=0.15,
            n_iter_no_change=8,
        )
        model.fit(x_train_flat, y_train)
        val_score = model.score(x_val_flat, y_val) if len(x_val_flat) > 0 else float("nan")
        joblib.dump(model, FALLBACK_MODEL_PATH)
        print("Modelo de respaldo guardado en:", FALLBACK_MODEL_PATH)
        print("Score validación respaldo (R^2):", val_score)

    joblib.dump(scaler_x, SCALER_X_PATH)
    joblib.dump(scaler_y, SCALER_PATH)
    print("Scaler X guardado en:", SCALER_X_PATH)
    print("Scaler guardado en:", SCALER_PATH)

if __name__ == "__main__":
    train()
