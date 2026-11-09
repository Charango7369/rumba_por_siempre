from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.rbac import usuarios_roles

BOLIVIA_TZ = timezone(timedelta(hours=-4))

def get_bolivia_now():
    return datetime.now(BOLIVIA_TZ)

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    rol = Column(String(50), nullable=True, default="comercial")
    activo = Column(Boolean, default=True, index=True)

    ultimo_acceso = Column(DateTime(timezone=True), nullable=True)
    creado_en = Column(DateTime(timezone=True), default=get_bolivia_now, server_default=func.now(), nullable=False)
    actualizado_en = Column(DateTime(timezone=True), default=get_bolivia_now, onupdate=get_bolivia_now, server_default=func.now(), nullable=False)

    roles = relationship("Rol", secondary=usuarios_roles, backref="usuarios", lazy="joined")
    refresh_tokens = relationship("RefreshToken", back_populates="usuario", cascade="all, delete-orphan")
