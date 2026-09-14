from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class Evento(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    fecha = Column(DateTime, nullable=True)
    lugar = Column(String, nullable=True)
    descripcion = Column(String, nullable=True)