import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.auditoria import Auditoria
from app.models.usuario import Usuario

logger = logging.getLogger("auditoria")

def registrar_auditoria(
    db: Session,
    usuario: Usuario,
    accion: str,
    recurso: str,
    recurso_id: Optional[str],
    ip: str,
    valores_previos: Optional[Dict[str, Any]] = None,
    valores_nuevos: Optional[Dict[str, Any]] = None,
    user_agent: Optional[str] = None
) -> Auditoria:
    """Registra una operación administrativa en la tabla inmutable de auditoría."""
    try:
        rol_nombre = "sin_rol"
        if usuario.roles:
            rol_nombre = usuario.roles[0].codigo
        elif usuario.rol:
            rol_nombre = usuario.rol

        log_entry = Auditoria(
            usuario_id=usuario.id,
            usuario_email=usuario.email,
            rol_ejecutor=rol_nombre,
            accion=accion,
            recurso_afectado=recurso,
            recurso_id=str(recurso_id) if recurso_id is not None else None,
            valores_previos=valores_previos,
            valores_nuevos=valores_nuevos,
            ip=ip,
            user_agent=user_agent[:250] if user_agent else None
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry
    except Exception as e:
        db.rollback()
        logger.error(f"Error al guardar log de auditoría: {e}")
        return None
