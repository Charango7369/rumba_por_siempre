from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.auditoria import Auditoria
from app.schemas.auditoria import AuditoriaResponse
from app.core.dependencies import require_role

router = APIRouter(prefix="/admin/audit", tags=["Admin Auditoría (SuperAdmin)"])

@router.get("", response_model=List[AuditoriaResponse], dependencies=[Depends(require_role(["superadmin"]))])
def listar_auditorias(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    accion: Optional[str] = None,
    recurso: Optional[str] = None,
    email: Optional[str] = None
):
    query = db.query(Auditoria)
    if accion:
        query = query.filter(Auditoria.accion.ilike(f"%{accion.strip()}%"))
    if recurso:
        query = query.filter(Auditoria.recurso_afectado.ilike(recurso.strip()))
    if email:
        query = query.filter(Auditoria.usuario_email.ilike(f"%{email.strip()}%"))

    return query.order_by(Auditoria.fecha_hora.desc()).offset(skip).limit(limit).all()
