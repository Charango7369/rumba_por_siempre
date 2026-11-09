from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, String, Text, DateTime, func
from app.database import Base

BOLIVIA_TZ = timezone(timedelta(hours=-4))

def get_bolivia_now():
    return datetime.now(BOLIVIA_TZ)

class Configuracion(Base):
    __tablename__ = "configuraciones"

    clave = Column(String(80), primary_key=True, index=True)
    valor = Column(Text, nullable=False)
    tipo_dato = Column(String(30), default="string", nullable=False)
    descripcion = Column(String(255), nullable=True)
    fecha_actualizacion = Column(DateTime(timezone=True), default=get_bolivia_now, onupdate=get_bolivia_now, server_default=func.now(), nullable=False)
