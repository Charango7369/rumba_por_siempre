from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.servicio import Servicio
from app.schemas.servicio import ServicioResponse, OpcionCotizacionResponse

router = APIRouter(prefix="/services", tags=["Catálogo Público"])

@router.get("", response_model=List[ServicioResponse])
def listar_servicios(
    db: Session = Depends(get_db),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría (Sonido, Iluminación, Paquetes)"),
    es_extra: Optional[bool] = Query(None, description="Filtrar por servicios principales o extras")
):
    query = db.query(Servicio).filter(Servicio.activo == True)
    if categoria:
        query = query.filter(Servicio.categoria.ilike(categoria.strip()))
    if es_extra is not None:
        query = query.filter(Servicio.es_extra == es_extra)

    return query.order_by(Servicio.orden_visualizacion.asc(), Servicio.id.asc()).all()

@router.get("/featured", response_model=List[ServicioResponse])
def listar_servicios_destacados(db: Session = Depends(get_db)):
    return db.query(Servicio).filter(
        Servicio.activo == True,
        Servicio.destacado == True
    ).order_by(Servicio.orden_visualizacion.asc()).all()

@router.get("/catalog/quote-options", response_model=OpcionCotizacionResponse)
def opciones_para_cotizador(db: Session = Depends(get_db)):
    paquetes = db.query(Servicio).filter(
        Servicio.activo == True,
        Servicio.es_extra == False
    ).order_by(Servicio.orden_visualizacion.asc()).all()

    extras = db.query(Servicio).filter(
        Servicio.activo == True,
        Servicio.es_extra == True
    ).order_by(Servicio.orden_visualizacion.asc()).all()

    return OpcionCotizacionResponse(paquetes=paquetes, extras=extras)

@router.get("/{id_or_slug}", response_model=ServicioResponse)
def detalle_servicio(id_or_slug: str, db: Session = Depends(get_db)):
    query = db.query(Servicio).filter(Servicio.activo == True)
    if id_or_slug.isdigit():
        servicio = query.filter(Servicio.id == int(id_or_slug)).first()
    else:
        servicio = query.filter(Servicio.slug == id_or_slug.strip().lower()).first()

    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado en el catálogo activo."
        )
    return servicio
