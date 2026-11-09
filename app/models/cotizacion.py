from datetime import datetime, timezone, timedelta
from sqlalchemy import (
    Column, Integer, String, Text, Numeric, Date, DateTime, ForeignKey, Index, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base

BOLIVIA_TZ = timezone(timedelta(hours=-4))

def get_bolivia_now():
    return datetime.now(BOLIVIA_TZ)

class Cotizacion(Base):
    __tablename__ = "cotizaciones"

    id = Column(Integer, primary_key=True, index=True)
    codigo_seguimiento = Column(String(30), unique=True, index=True, nullable=True)
    nombre = Column(String(100), nullable=False)
    telefono = Column(String(30), nullable=False, index=True)
    ciudad = Column(String(80), nullable=False)
    fecha_evento = Column(Date, nullable=False, index=True)
    tipo_evento = Column(String(60), nullable=False)
    invitados = Column(Integer, nullable=False)

    paquete = Column(String(80), nullable=False)
    extras = Column(JSONB, nullable=False, default=list)

    servicio_id = Column(Integer, ForeignKey("servicios.id", ondelete="SET NULL"), nullable=True)
    total_estimado = Column(Numeric(10, 2), nullable=True)
    desglose_calculo = Column(JSONB, nullable=True)

    estado = Column(String(30), default="Pendiente", nullable=False, index=True)
    observaciones = Column(Text, nullable=True)
    atendido_por_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)

    timestamp = Column(DateTime(timezone=True), default=get_bolivia_now, server_default=func.now(), nullable=False, index=True)
    actualizado_en = Column(DateTime(timezone=True), default=get_bolivia_now, onupdate=get_bolivia_now, server_default=func.now(), nullable=False)

    servicio = relationship("Servicio")
    operador = relationship("Usuario")

    __table_args__ = (
        Index("idx_cotiz_estado_fecha", "estado", "fecha_evento"),
    )
