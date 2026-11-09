"""Migracion integral RBAC, Catalogo administrable, Auditoria y Cotizaciones

Revision ID: 001_initial_rbac
Revises: 
Create Date: 2026-11-09 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial_rbac'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Tabla Permisos
    op.execute("""
    CREATE TABLE IF NOT EXISTS permisos (
        id SERIAL PRIMARY KEY,
        codigo VARCHAR(80) NOT NULL UNIQUE,
        modulo VARCHAR(50) NOT NULL,
        descripcion VARCHAR(200) NOT NULL
    );
    CREATE INDEX IF NOT EXISTS ix_permisos_codigo ON permisos (codigo);
    CREATE INDEX IF NOT EXISTS ix_permisos_modulo ON permisos (modulo);
    """)

    # 2. Tabla Roles
    op.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id SERIAL PRIMARY KEY,
        codigo VARCHAR(50) NOT NULL UNIQUE,
        nombre VARCHAR(100) NOT NULL,
        descripcion TEXT,
        es_sistema BOOLEAN NOT NULL DEFAULT FALSE
    );
    CREATE INDEX IF NOT EXISTS ix_roles_codigo ON roles (codigo);
    """)

    # 3. Tablas intermedias RBAC
    op.execute("""
    CREATE TABLE IF NOT EXISTS roles_permisos (
        rol_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
        permiso_id INTEGER NOT NULL REFERENCES permisos(id) ON DELETE CASCADE,
        PRIMARY KEY (rol_id, permiso_id)
    );

    CREATE TABLE IF NOT EXISTS usuarios_roles (
        usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        rol_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
        PRIMARY KEY (usuario_id, rol_id)
    );
    """)

    # 4. Tabla Refresh Tokens
    op.execute("""
    CREATE TABLE IF NOT EXISTS refresh_tokens (
        id SERIAL PRIMARY KEY,
        usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        token_hash VARCHAR(255) NOT NULL UNIQUE,
        fecha_expiracion TIMESTAMPTZ NOT NULL,
        revocado BOOLEAN NOT NULL DEFAULT FALSE,
        creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS ix_refresh_tokens_token_hash ON refresh_tokens (token_hash);
    CREATE INDEX IF NOT EXISTS ix_refresh_tokens_usuario_id ON refresh_tokens (usuario_id);
    """)

    # 5. Tabla Auditoria
    op.execute("""
    CREATE TABLE IF NOT EXISTS auditorias (
        id BIGSERIAL PRIMARY KEY,
        usuario_id INTEGER,
        usuario_email VARCHAR(150) NOT NULL,
        rol_ejecutor VARCHAR(60) NOT NULL,
        accion VARCHAR(80) NOT NULL,
        recurso_afectado VARCHAR(80) NOT NULL,
        recurso_id VARCHAR(80),
        valores_previos JSONB,
        valores_nuevos JSONB,
        ip VARCHAR(45) NOT NULL,
        user_agent VARCHAR(255),
        fecha_hora TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_audit_recurso_fecha ON auditorias (recurso_afectado, fecha_hora);
    """)

    # 6. Tabla Configuraciones
    op.execute("""
    CREATE TABLE IF NOT EXISTS configuraciones (
        clave VARCHAR(80) PRIMARY KEY,
        valor TEXT NOT NULL,
        tipo_dato VARCHAR(30) NOT NULL DEFAULT 'string',
        descripcion VARCHAR(255),
        fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """)

    # 7. Expandir tabla 'usuarios'
    op.execute("""
    ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS ultimo_acceso TIMESTAMPTZ;
    ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS actualizado_en TIMESTAMPTZ DEFAULT NOW();
    """)

    # 8. Expandir tabla 'servicios'
    op.execute("""
    ALTER TABLE servicios ADD COLUMN IF NOT EXISTS slug VARCHAR(120);
    ALTER TABLE servicios ADD COLUMN IF NOT EXISTS descripcion_corta VARCHAR(255);
    ALTER TABLE servicios ADD COLUMN IF NOT EXISTS descripcion_larga TEXT;
    ALTER TABLE servicios ADD COLUMN IF NOT EXISTS precio_promocional NUMERIC(10, 2);
    ALTER TABLE servicios ADD COLUMN IF NOT EXISTS imagen_principal VARCHAR(500) DEFAULT '';
    ALTER TABLE servicios ADD COLUMN IF NOT EXISTS galeria_imagenes JSONB DEFAULT '[]'::jsonb;
    ALTER TABLE servicios ADD COLUMN IF NOT EXISTS especificaciones_tecnicas JSONB DEFAULT '[]'::jsonb;
    ALTER TABLE servicios ADD COLUMN IF NOT EXISTS es_extra BOOLEAN DEFAULT FALSE;
    ALTER TABLE servicios ADD COLUMN IF NOT EXISTS activo BOOLEAN DEFAULT TRUE;
    ALTER TABLE servicios ADD COLUMN IF NOT EXISTS destacado BOOLEAN DEFAULT FALSE;
    ALTER TABLE servicios ADD COLUMN IF NOT EXISTS orden_visualizacion INTEGER DEFAULT 0;
    ALTER TABLE servicios ADD COLUMN IF NOT EXISTS fecha_creacion TIMESTAMPTZ DEFAULT NOW();
    ALTER TABLE servicios ADD COLUMN IF NOT EXISTS fecha_actualizacion TIMESTAMPTZ DEFAULT NOW();

    -- Generar slugs para registros anteriores que no tengan
    UPDATE servicios SET slug = LOWER(REPLACE(nombre, ' ', '-')) WHERE slug IS NULL;
    """)

    # Crear indices si no existen
    op.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS ix_servicios_slug ON servicios (slug);
    CREATE INDEX IF NOT EXISTS idx_servicios_activo_orden ON servicios (activo, orden_visualizacion);
    CREATE INDEX IF NOT EXISTS idx_servicios_categoria_activo ON servicios (categoria, activo);
    CREATE INDEX IF NOT EXISTS idx_servicios_es_extra_activo ON servicios (es_extra, activo);
    """)

    # 9. Expandir tabla 'cotizaciones'
    op.execute("""
    ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS codigo_seguimiento VARCHAR(30);
    ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS servicio_id INTEGER REFERENCES servicios(id) ON DELETE SET NULL;
    ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS total_estimado NUMERIC(10, 2);
    ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS desglose_calculo JSONB;
    ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS estado VARCHAR(30) DEFAULT 'Pendiente';
    ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS observaciones TEXT;
    ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS atendido_por_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL;
    ALTER TABLE cotizaciones ADD COLUMN IF NOT EXISTS actualizado_en TIMESTAMPTZ DEFAULT NOW();

    -- Generar códigos de seguimiento para cotizaciones existentes
    UPDATE cotizaciones SET codigo_seguimiento = 'RXS-HIST-' || id WHERE codigo_seguimiento IS NULL;
    """)

    op.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS ix_cotizaciones_codigo_seguimiento ON cotizaciones (codigo_seguimiento);
    CREATE INDEX IF NOT EXISTS idx_cotiz_estado_fecha ON cotizaciones (estado, fecha_evento);
    """)

def downgrade() -> None:
    pass
