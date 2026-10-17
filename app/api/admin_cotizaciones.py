"""Base del dashboard: GET /api/admin/cotizaciones (se monta con prefix="/api" en main.py)."""
import os
import secrets
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.cotizacion import Cotizacion

router = APIRouter(prefix="/admin", tags=["admin-cotizaciones"])


def require_admin(x_admin_token: str = Header(default="")) -> None:
    """TEMPORAL: sustituir por la dependencia de auth que ya use tu modelo Usuario (JWT/sesión)."""
    esperado = os.getenv("ADMIN_API_TOKEN", "")
    if not esperado or not secrets.compare_digest(x_admin_token, esperado):
        raise HTTPException(status_code=401, detail="No autorizado")


class CotizacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    telefono: str
    ciudad: str
    fecha_evento: date
    tipo_evento: str
    invitados: int
    paquete: str
    extras: List[str]
    timestamp: datetime


@router.get("/cotizaciones", response_model=List[CotizacionOut], dependencies=[Depends(require_admin)])
def listar(db: Session = Depends(get_db), skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
           ciudad: Optional[str] = None, paquete: Optional[str] = None):
    q = db.query(Cotizacion)
    if ciudad:
        q = q.filter(Cotizacion.ciudad.ilike(f"%{ciudad}%"))
    if paquete:
        q = q.filter(Cotizacion.paquete == paquete.lower())
    return q.order_by(Cotizacion.timestamp.desc()).offset(skip).limit(limit).all()
