from datetime import datetime, timezone, timedelta
from sqlalchemy import (
    Column, Integer, String, Text, Numeric, Boolean, DateTime, func, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base

BOLIVIA_TZ = timezone(timedelta(hours=-4))

def get_bolivia_now():
    """Genera la marca de tiempo en hora boliviana (UTC-4) sin dependencias externas."""
    return datetime.now(BOLIVIA_TZ)

class Servicio(Base):
    __tablename__ = "servicios"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(120), unique=True, nullable=False, index=True)
    nombre = Column(String(120), nullable=False, index=True)
    categoria = Column(String(60), nullable=False, index=True)  # Sonido, Iluminación, Paquetes, Efectos
    descripcion_corta = Column(String(255), nullable=True)
    descripcion_larga = Column(Text, nullable=True)

    precio_base = Column(Numeric(10, 2), nullable=False, default=0.00)
    precio_promocional = Column(Numeric(10, 2), nullable=True)

    imagen_principal = Column(String(500), nullable=False)
    galeria_imagenes = Column(JSONB, nullable=False, default=list)
    especificaciones_tecnicas = Column(JSONB, nullable=False, default=list)

    es_extra = Column(Boolean, default=False, index=True)
    activo = Column(Boolean, default=True, index=True)
    destacado = Column(Boolean, default=False, index=True)
    orden_visualizacion = Column(Integer, default=0, index=True)

    fecha_creacion = Column(DateTime(timezone=True), default=get_bolivia_now, server_default=func.now(), nullable=False)
    fecha_actualizacion = Column(DateTime(timezone=True), default=get_bolivia_now, onupdate=get_bolivia_now, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_servicios_activo_orden", "activo", "orden_visualizacion"),
        Index("idx_servicios_categoria_activo", "categoria", "activo"),
        Index("idx_servicios_es_extra_activo", "es_extra", "activo"),
    )
