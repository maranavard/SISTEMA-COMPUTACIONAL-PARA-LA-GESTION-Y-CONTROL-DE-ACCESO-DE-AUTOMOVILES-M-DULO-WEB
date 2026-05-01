import pandas as pd
from pathlib import Path

IA_DIR = Path(__file__).resolve().parent
CSV_PATH = IA_DIR / 'ocupacion_5min.csv'

# Cargar el archivo CSV
df = pd.read_csv(CSV_PATH)

# Mostrar las primeras filas
print(df.head())

# Mostrar la forma del DataFrame (filas, columnas)
print("Número de filas y columnas:", df.shape)
