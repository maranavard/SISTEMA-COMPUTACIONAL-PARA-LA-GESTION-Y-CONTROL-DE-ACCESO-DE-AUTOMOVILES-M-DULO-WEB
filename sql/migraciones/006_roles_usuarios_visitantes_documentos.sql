-- 006_roles_usuarios_visitantes_documentos.sql
-- Extensión de esquema para Sprint 1 (auth, roles, conductores, visitantes, documentos y sincronización)

BEGIN;

CREATE TABLE IF NOT EXISTS public.roles (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(30) UNIQUE NOT NULL,
    nombre VARCHAR(80) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

INSERT INTO public.roles (codigo, nombre)
VALUES
    ('admin_sistema', 'Administrador del sistema'),
    ('seguridad_udec', 'Personal de seguridad'),
    ('funcionario_area', 'Funcionario administrativo'),
    ('conductor_udec', 'Conductor UDEC'),
    ('propietario', 'Propietario')
ON CONFLICT (codigo) DO NOTHING;

CREATE TABLE IF NOT EXISTS public.usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol_id INTEGER NOT NULL REFERENCES public.roles(id),
    estado VARCHAR(20) NOT NULL DEFAULT 'activo',
    nombres VARCHAR(120) NOT NULL,
    apellidos VARCHAR(120) NOT NULL,
    numero_identificacion VARCHAR(30) UNIQUE,
    dependencia VARCHAR(120),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_usuarios_estado'
    ) THEN
        ALTER TABLE public.usuarios
        ADD CONSTRAINT chk_usuarios_estado
        CHECK (estado IN ('activo', 'inactivo', 'bloqueado'));
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS public.conductores (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL UNIQUE REFERENCES public.usuarios(id) ON DELETE CASCADE,
    telefono VARCHAR(30),
    tipo_conductor VARCHAR(30) NOT NULL DEFAULT 'estudiante',
    numero_pase VARCHAR(50),
    categoria_pase VARCHAR(20),
    fecha_registro_pase DATE,
    fecha_vencimiento_pase DATE,
    estado VARCHAR(20) NOT NULL DEFAULT 'activo',
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_conductores_tipo'
    ) THEN
        ALTER TABLE public.conductores
        ADD CONSTRAINT chk_conductores_tipo
        CHECK (tipo_conductor IN ('estudiante', 'docente', 'visitante', 'funcionario', 'otro'));
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_conductores_estado'
    ) THEN
        ALTER TABLE public.conductores
        ADD CONSTRAINT chk_conductores_estado
        CHECK (estado IN ('activo', 'inactivo'));
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS public.visitantes (
    id SERIAL PRIMARY KEY,
    nombres VARCHAR(120) NOT NULL,
    apellidos VARCHAR(120) NOT NULL,
    numero_identificacion VARCHAR(30) NOT NULL,
    area_destino VARCHAR(120) NOT NULL,
    motivo_visita TEXT,
    placa VARCHAR(20),
    fecha_hora_registro TIMESTAMP NOT NULL DEFAULT now(),
    fecha_hora_prevista TIMESTAMP NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    registrado_por_usuario_id INTEGER NOT NULL REFERENCES public.usuarios(id),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_visitantes_estado'
    ) THEN
        ALTER TABLE public.visitantes
        ADD CONSTRAINT chk_visitantes_estado
        CHECK (estado IN ('pendiente', 'autorizado', 'rechazado', 'ingresado', 'finalizado'));
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_visitantes_doc ON public.visitantes (numero_identificacion);
CREATE INDEX IF NOT EXISTS idx_visitantes_estado_fecha ON public.visitantes (estado, fecha_hora_prevista);

CREATE TABLE IF NOT EXISTS public.autorizaciones_visitante (
    id SERIAL PRIMARY KEY,
    visitante_id INTEGER NOT NULL REFERENCES public.visitantes(id) ON DELETE CASCADE,
    autorizado_por_usuario_id INTEGER NOT NULL REFERENCES public.usuarios(id),
    estado VARCHAR(20) NOT NULL,
    observacion TEXT,
    fecha_decision TIMESTAMP NOT NULL DEFAULT now()
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_autorizaciones_estado'
    ) THEN
        ALTER TABLE public.autorizaciones_visitante
        ADD CONSTRAINT chk_autorizaciones_estado
        CHECK (estado IN ('autorizado', 'rechazado'));
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_autorizaciones_visitante ON public.autorizaciones_visitante (visitante_id);

CREATE TABLE IF NOT EXISTS public.tipo_documento (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(30) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    entidad_objetivo VARCHAR(30) NOT NULL DEFAULT 'vehiculo',
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

INSERT INTO public.tipo_documento (codigo, nombre, entidad_objetivo)
VALUES
    ('soat', 'SOAT', 'vehiculo'),
    ('tecnomecanica', 'Técnico-mecánica', 'vehiculo'),
    ('tarjeta_propiedad', 'Tarjeta de propiedad', 'vehiculo'),
    ('licencia_conduccion', 'Licencia de conducción', 'conductor')
ON CONFLICT (codigo) DO NOTHING;

CREATE TABLE IF NOT EXISTS public.documentos_vehiculo (
    id SERIAL PRIMARY KEY,
    vehiculo_id INTEGER NOT NULL REFERENCES public.vehiculos(id) ON DELETE CASCADE,
    tipo_documento_id INTEGER NOT NULL REFERENCES public.tipo_documento(id),
    archivo_url TEXT,
    fecha_registro DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_vencimiento DATE,
    estado VARCHAR(20) NOT NULL DEFAULT 'vigente',
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    UNIQUE (vehiculo_id, tipo_documento_id)
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_doc_vehiculo_estado'
    ) THEN
        ALTER TABLE public.documentos_vehiculo
        ADD CONSTRAINT chk_doc_vehiculo_estado
        CHECK (estado IN ('vigente', 'vencido', 'por_vencer', 'invalido'));
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_doc_vehiculo_venc ON public.documentos_vehiculo (fecha_vencimiento);

CREATE TABLE IF NOT EXISTS public.sync_pendientes (
    id BIGSERIAL PRIMARY KEY,
    tabla_origen VARCHAR(80) NOT NULL,
    registro_id BIGINT,
    tipo_operacion VARCHAR(10) NOT NULL,
    payload JSONB NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    intentos INTEGER NOT NULL DEFAULT 0,
    ultimo_error TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_sync_operacion'
    ) THEN
        ALTER TABLE public.sync_pendientes
        ADD CONSTRAINT chk_sync_operacion
        CHECK (tipo_operacion IN ('INSERT', 'UPDATE', 'DELETE'));
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_sync_estado'
    ) THEN
        ALTER TABLE public.sync_pendientes
        ADD CONSTRAINT chk_sync_estado
        CHECK (estado IN ('pendiente', 'enviado', 'error'));
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_sync_estado_intentos ON public.sync_pendientes (estado, intentos, created_at);

COMMIT;