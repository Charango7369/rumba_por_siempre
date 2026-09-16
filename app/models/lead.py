from sqlalchemy import Column, Integer, String, Date, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from zoneinfo import ZoneInfo
from app.database import Base

def get_bolivia_time():
    """Genera la marca de tiempo exacta en UTC-4"""
    return datetime.now(ZoneInfo("America/La_Paz"))

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    telefono = Column(String(20), nullable=False)
    tipo_evento = Column(String(50), nullable=False)
    fecha_estimada = Column(Date, nullable=False)
    
    # Ciclo de vida del dato
    estado = Column(String(20), default="Pendiente")
    creado_en = Column(DateTime(timezone=True), default=get_bolivia_time)
    # Dentro de la clase Lead:
    servicio_id = Column(Integer, ForeignKey("servicios.id"), nullable=True)
    servicio_interes = relationship("Servicio")

    # Restricción matemática contra duplicados en la base de datos
    __table_args__ = (
        UniqueConstraint('telefono', 'fecha_estimada', name='uq_telefono_fecha'),
    )