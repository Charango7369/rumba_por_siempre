from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, BigInteger, Integer, String, DateTime, Index, func
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base

BOLIVIA_TZ = timezone(timedelta(hours=-4))

def get_bolivia_now():
    return datetime.now(BOLIVIA_TZ)

class Auditoria(Base):
    __tablename__ = "auditorias"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, nullable=True, index=True)
    usuario_email = Column(String(150), nullable=False, index=True)
    rol_ejecutor = Column(String(60), nullable=False)
    accion = Column(String(80), nullable=False, index=True)
    recurso_afectado = Column(String(80), nullable=False, index=True)
    recurso_id = Column(String(80), nullable=True)

    valores_previos = Column(JSONB, nullable=True)
    valores_nuevos = Column(JSONB, nullable=True)

    ip = Column(String(45), nullable=False)
    user_agent = Column(String(255), nullable=True)
    fecha_hora = Column(DateTime(timezone=True), default=get_bolivia_now, server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("idx_audit_recurso_fecha", "recurso_afectado", "fecha_hora"),
    )
