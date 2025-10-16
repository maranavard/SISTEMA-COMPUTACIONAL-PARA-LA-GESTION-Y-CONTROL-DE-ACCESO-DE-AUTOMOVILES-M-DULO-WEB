import pandas as pd

# Cargar el archivo CSV
df = pd.read_csv('ocupacion_5min.csv')

# Mostrar las primeras filas
print(df.head())

# Mostrar la forma del DataFrame (filas, columnas)
print("Número de filas y columnas:", df.shape)
