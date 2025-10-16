import pandas as pd
from sqlalchemy import create_engine

# 1️⃣ Conexión a la base de datos PostgreSQL
engine = create_engine('postgresql+psycopg2://postgres:12345@localhost:5432/sistema_control')

# 2️⃣ Consulta SQL: extrae registros de entrada/salida
query = """
SELECT 
    rv.id,
    rv.id_vehiculo,
    rv.fecha_registro AS timestamp,
    rv.concepto
FROM registro_visitantes rv
ORDER BY rv.fecha_registro ASC;
"""


# 3️⃣ Leer los datos
df = pd.read_sql(query, engine)
print("Total de registros:", len(df))

# 4️⃣ Normalizar los datos y crear serie temporal
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)
df.sort_index(inplace=True)

# Ventana de tiempo de 5 minutos
idx = pd.date_range(df.index.min().floor('5min'), df.index.max().ceil('5min'), freq='5min')
serie = pd.Series(0, index=idx)

# Calcular ocupación (acumulada)
ocupados = 0
for t, row in df.iterrows():
    if row['concepto'].lower() == 'entrada':
        ocupados += 1
    elif row['concepto'].lower() == 'salida':
        ocupados -= 1
    serie.loc[t:] = max(0, ocupados)

# 5️⃣ Crear DataFrame final
df_ocupacion = pd.DataFrame({
    'timestamp': serie.index,
    'ocupados': serie.values
})
df_ocupacion['hora'] = df_ocupacion['timestamp'].dt.hour
df_ocupacion['dia_semana'] = df_ocupacion['timestamp'].dt.dayofweek

# 6️⃣ Guardar CSV
df_ocupacion.to_csv('ocupacion_5min.csv', index=False)
print("Archivo generado: ocupacion_5min.csv")
