from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from zoneinfo import ZoneInfo
from app.database import Base

def get_bolivia_time():
    """Genera la marca de tiempo exacta en UTC-4"""
    return datetime.now(ZoneInfo("America/La_Paz"))

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    rol = Column(String(20), default="empleado") # roles: "admin", "empleado"
    activo = Column(Boolean, default=True)
    
    creado_en = Column(DateTime(timezone=True), default=get_bolivia_time)