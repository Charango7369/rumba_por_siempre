from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base

BOLIVIA_TZ = timezone(timedelta(hours=-4))

def get_bolivia_now():
    return datetime.now(BOLIVIA_TZ)

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    fecha_expiracion = Column(DateTime(timezone=True), nullable=False)
    revocado = Column(Boolean, default=False, nullable=False)
    creado_en = Column(DateTime(timezone=True), default=get_bolivia_now, server_default=func.now(), nullable=False)

    usuario = relationship("Usuario", back_populates="refresh_tokens")
