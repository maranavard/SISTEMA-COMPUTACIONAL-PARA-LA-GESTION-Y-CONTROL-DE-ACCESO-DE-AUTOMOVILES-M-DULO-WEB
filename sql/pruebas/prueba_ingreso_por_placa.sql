INSERT INTO novedad (tipo_novedad, id_vehiculo, id_usuario, observaciones)
VALUES (
  'ingreso',
  (SELECT id FROM vehiculos WHERE placa = 'XYZ987' LIMIT 1),
  3,
  'Ingreso por portería test'
);
