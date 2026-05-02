-- 02_recuperar_acceso_login.sql
-- Objetivo: recuperar acceso al login del módulo web.
-- Ejecutar en PostgreSQL (BD: sistema_control) desde pgAdmin Query Tool.

CREATE OR REPLACE FUNCTION pg_temp.has_usuarios_column(p_column text)
RETURNS boolean
LANGUAGE sql
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'usuarios'
      AND column_name = p_column
  );
$$;

CREATE OR REPLACE FUNCTION pg_temp.has_public_table(p_table text)
RETURNS boolean
LANGUAGE sql
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_name = p_table
  );
$$;

-- =========================================================
-- PASO 1) Ver qué columnas tiene la tabla usuarios
-- =========================================================
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'usuarios'
ORDER BY ordinal_position;

-- =========================================================
-- PASO 2) Listar usuarios existentes (para recordar username)
-- =========================================================
-- Nota: según tu esquema, puede existir role / rol_id / idrol.
SELECT
  u.id,
  u.username,
  CASE WHEN pg_temp.has_usuarios_column('estado') THEN u.estado::text ELSE 'N/A' END AS estado,
  CASE WHEN pg_temp.has_usuarios_column('role') THEN COALESCE(u.role::text,'') ELSE '' END AS role_text
FROM public.usuarios u
ORDER BY u.id;

-- =========================================================
-- PASO 3A) (RECOMENDADO) Resetear contraseña de un usuario existente
-- =========================================================
-- 1) Reemplaza 'TU_USUARIO' por un username real del paso 2.
-- 2) Reemplaza 'Admin123*' por tu nueva contraseña temporal.
--
-- Como el backend actual soporta texto plano o hash, esto funciona de inmediato.
UPDATE public.usuarios
SET password = 'Admin123*'
WHERE username = 'TU_USUARIO';

-- Activar usuario si existe columna estado
DO $$
BEGIN
  IF pg_temp.has_usuarios_column('estado') THEN
    EXECUTE 'UPDATE public.usuarios SET estado = ''activo'' WHERE username = ''TU_USUARIO''';
  END IF;
END $$;

-- =========================================================
-- PASO 3B) (ALTERNATIVO) Crear admin temporal si no tienes usuarios
-- =========================================================
-- Este bloque solo crea usuario si la tabla usuarios está vacía.
-- Usuario: admin_tmp
-- Clave: Admin123*
DO $$
DECLARE
  v_total INTEGER;
  v_has_role BOOLEAN;
  v_role_is_array BOOLEAN;
  v_has_estado BOOLEAN;
  v_has_nombre BOOLEAN;
  v_has_apellido BOOLEAN;
  v_has_email BOOLEAN;
  v_has_rol_id BOOLEAN;
  v_admin_role_id INTEGER;
BEGIN
  SELECT COUNT(*) INTO v_total FROM public.usuarios;

  IF v_total = 0 THEN
    SELECT pg_temp.has_usuarios_column('role') INTO v_has_role;

    SELECT EXISTS (
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema='public'
        AND table_name='usuarios'
        AND column_name='role'
        AND data_type = 'ARRAY'
    ) INTO v_role_is_array;

    SELECT pg_temp.has_usuarios_column('estado') INTO v_has_estado;
    SELECT pg_temp.has_usuarios_column('nombre') INTO v_has_nombre;
    SELECT pg_temp.has_usuarios_column('apellido') INTO v_has_apellido;
    SELECT pg_temp.has_usuarios_column('email') INTO v_has_email;

    SELECT EXISTS (
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema='public'
        AND table_name='usuarios'
        AND column_name IN ('rol_id','idrol')
    ) INTO v_has_rol_id;

    -- Si existe tabla roles, intenta usar admin_sistema.
    IF pg_temp.has_public_table('roles') THEN
      SELECT id
      INTO v_admin_role_id
      FROM public.roles
      WHERE codigo IN ('admin_sistema', 'admin', 'administrador')
      ORDER BY id
      LIMIT 1;
    END IF;

    -- Inserción base mínima
    EXECUTE 'INSERT INTO public.usuarios (username, password) VALUES (''admin_tmp'', ''Admin123*'')';

    IF v_has_role THEN
      IF v_role_is_array THEN
        EXECUTE 'UPDATE public.usuarios SET role = ARRAY[''admin_sistema''] WHERE username = ''admin_tmp''';
      ELSE
        EXECUTE 'UPDATE public.usuarios SET role = ''admin_sistema'' WHERE username = ''admin_tmp''';
      END IF;
    END IF;

    IF v_has_estado THEN
      EXECUTE 'UPDATE public.usuarios SET estado = ''activo'' WHERE username = ''admin_tmp''';
    END IF;

    IF v_has_nombre THEN
      EXECUTE 'UPDATE public.usuarios SET nombre = ''Admin'' WHERE username = ''admin_tmp''';
    END IF;

    IF v_has_apellido THEN
      EXECUTE 'UPDATE public.usuarios SET apellido = ''Temporal'' WHERE username = ''admin_tmp''';
    END IF;

    IF v_has_email THEN
      EXECUTE 'UPDATE public.usuarios SET email = ''admin_tmp@udec.local'' WHERE username = ''admin_tmp''';
    END IF;

    IF v_has_rol_id AND v_admin_role_id IS NOT NULL THEN
      IF pg_temp.has_usuarios_column('rol_id') THEN
        EXECUTE format('UPDATE public.usuarios SET rol_id = %s WHERE username = ''admin_tmp''', v_admin_role_id);
      ELSIF pg_temp.has_usuarios_column('idrol') THEN
        EXECUTE format('UPDATE public.usuarios SET idrol = %s WHERE username = ''admin_tmp''', v_admin_role_id);
      END IF;
    END IF;
  END IF;
END $$;

-- =========================================================
-- PASO 4) Verificación final
-- =========================================================
SELECT id, username,
       CASE WHEN pg_temp.has_usuarios_column('estado') THEN estado::text ELSE 'N/A' END AS estado,
       CASE WHEN pg_temp.has_usuarios_column('role') THEN COALESCE(role::text,'') ELSE '' END AS role_text
FROM public.usuarios
ORDER BY id;

-- Después del login exitoso:
-- 1) Cambia la contraseña temporal desde el módulo /usuarios.
-- 2) Si tocaste TU_USUARIO en el PASO 3A, deja solo ese paso y comenta el resto.
