from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from datetime import datetime
from zoneinfo import ZoneInfo
from app.database import Base

def get_bolivia_time():
    """Genera la marca de tiempo exacta en UTC-4"""
    return datetime.now(ZoneInfo("America/La_Paz"))

class Servicio(Base):
    __tablename__ = "servicios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), index=True, nullable=False)
    descripcion = Column(Text, nullable=True)
    precio_base = Column(Float, nullable=False, default=0.0)
    categoria = Column(String(50), nullable=True) # Ejemplo: "Sonido", "Iluminación", "Mobiliario"
    disponible = Column(Boolean, default=True)
    
    creado_en = Column(DateTime(timezone=True), default=get_bolivia_time)