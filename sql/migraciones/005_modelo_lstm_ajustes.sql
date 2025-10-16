-- Migración 004: Ajustes para modelo LSTM y asignaciones automáticas
-- Autor: Mara
-- Fecha: 2025-10-14

-- Crear tabla de predicciones automáticas
CREATE TABLE IF NOT EXISTS predicciones (
    id SERIAL PRIMARY KEY,
    fecha_generacion TIMESTAMP DEFAULT now(),
    horizonte_minutos INTEGER NOT NULL,
    paso INTEGER NOT NULL,
    timestamp_prediccion TIMESTAMP NOT NULL,
    espacios_libres_pred INTEGER NOT NULL,
    modelo_version VARCHAR(50) DEFAULT 'LSTM_v1'
);

-- Crear tabla para registrar asignaciones automáticas o manuales
CREATE TABLE IF NOT EXISTS asignaciones_log (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP DEFAULT now(),
    id_usuario INTEGER,
    id_vehiculo INTEGER,
    id_espacio INTEGER,
    metodo VARCHAR(20) DEFAULT 'automatica',
    motivo TEXT,
    estado VARCHAR(20) DEFAULT 'asignado'
);

-- Añadir columna de fecha_actualización a espacio (si no existe)
ALTER TABLE espacio
ADD COLUMN IF NOT EXISTS fecha_actualizacion TIMESTAMP DEFAULT now();
