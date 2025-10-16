
ALTER TABLE vehiculos ADD CONSTRAINT placa_unica UNIQUE (placa);
-- esta restricción previene errores de subconsulta múltiple.