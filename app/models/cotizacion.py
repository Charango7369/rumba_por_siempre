from sqlalchemy import JSON, Column, Date, DateTime, Integer, String, func

from app.database import Base


class Cotizacion(Base):
    __tablename__ = "cotizaciones"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(80), nullable=False)
    telefono = Column(String(20), nullable=False)
    ciudad = Column(String(80), nullable=False)
    fecha_evento = Column(Date, nullable=False, index=True)
    tipo_evento = Column(String(60), nullable=False)
    invitados = Column(Integer, nullable=False)
    paquete = Column(String(40), nullable=False)
    extras = Column(JSON, nullable=False, default=list)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
