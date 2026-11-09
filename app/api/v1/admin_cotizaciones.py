from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.cotizacion import Cotizacion
from app.models.usuario import Usuario
from app.schemas.cotizacion import CotizacionResponse, CotizacionStatusUpdate
from app.core.dependencies import require_permission, get_client_ip
from app.services.auditoria_service import registrar_auditoria

router = APIRouter(prefix="/admin/quotes", tags=["Admin Cotizaciones"])

@router.get("", response_model=List[CotizacionResponse], dependencies=[Depends(require_permission("quotes:read"))])
def admin_listar_cotizaciones(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    estado: Optional[str] = None,
    ciudad: Optional[str] = None,
    q: Optional[str] = None
):
    query = db.query(Cotizacion)
    if estado:
        query = query.filter(Cotizacion.estado.ilike(estado.strip()))
    if ciudad:
        query = query.filter(Cotizacion.ciudad.ilike(f"%{ciudad.strip()}%"))
    if q:
        termino = f"%{q.strip()}%"
        query = query.filter((Cotizacion.nombre.ilike(termino)) | (Cotizacion.telefono.ilike(termino)))

    return query.order_by(Cotizacion.timestamp.desc()).offset(skip).limit(limit).all()

@router.get("/{quote_id}", response_model=CotizacionResponse, dependencies=[Depends(require_permission("quotes:read"))])
def admin_detalle_cotizacion(quote_id: int, db: Session = Depends(get_db)):
    cotiz = db.query(Cotizacion).filter(Cotizacion.id == quote_id).first()
    if not cotiz:
        raise HTTPException(status_code=404, detail="Cotización no encontrada.")
    return cotiz

@router.patch("/{quote_id}", response_model=CotizacionResponse, dependencies=[Depends(require_permission("quotes:update_status"))])
def admin_actualizar_estado_cotizacion(
    quote_id: int,
    payload: CotizacionStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("quotes:update_status"))
):
    cotiz = db.query(Cotizacion).filter(Cotizacion.id == quote_id).first()
    if not cotiz:
        raise HTTPException(status_code=404, detail="Cotización no encontrada.")

    estado_anterior = cotiz.estado
    observaciones_anteriores = cotiz.observaciones

    cotiz.estado = payload.estado
    if payload.observaciones is not None:
        cotiz.observaciones = payload.observaciones
    cotiz.atendido_por_id = usuario.id

    db.commit()
    db.refresh(cotiz)

    registrar_auditoria(
        db=db,
        usuario=usuario,
        accion="CAMBIO_ESTADO_COTIZACION",
        recurso="cotizaciones",
        recurso_id=str(cotiz.id),
        ip=get_client_ip(request),
        valores_previos={"estado": estado_anterior, "observaciones": observaciones_anteriores},
        valores_nuevos={"estado": cotiz.estado, "observaciones": cotiz.observaciones},
        user_agent=request.headers.get("user-agent")
    )

    return cotiz

@router.delete("/{quote_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(require_permission("quotes:delete"))])
def admin_eliminar_cotizacion(
    quote_id: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("quotes:delete"))
):
    cotiz = db.query(Cotizacion).filter(Cotizacion.id == quote_id).first()
    if not cotiz:
        raise HTTPException(status_code=404, detail="Cotización no encontrada.")

    cliente = cotiz.nombre
    db.delete(cotiz)
    db.commit()

    registrar_auditoria(
        db=db,
        usuario=usuario,
        accion="ELIMINAR_COTIZACION",
        recurso="cotizaciones",
        recurso_id=str(quote_id),
        ip=get_client_ip(request),
        valores_previos={"cliente": cliente},
        user_agent=request.headers.get("user-agent")
    )

    return {"message": f"Cotización #{quote_id} de '{cliente}' eliminada."}
