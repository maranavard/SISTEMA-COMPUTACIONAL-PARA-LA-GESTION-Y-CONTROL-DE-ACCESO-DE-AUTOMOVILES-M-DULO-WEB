-- 03_verificar_conexion_web.sql
-- Ejecutar en pgAdmin para confirmar credenciales que debes poner en python/webapp/.env

SELECT
  current_database() AS db_actual,
  current_user AS usuario_actual,
  inet_server_addr() AS host_servidor,
  inet_server_port() AS puerto_servidor,
  (SELECT setting FROM pg_settings WHERE name = 'server_encoding') AS server_encoding,
  (SELECT setting FROM pg_settings WHERE name = 'client_encoding') AS client_encoding;
