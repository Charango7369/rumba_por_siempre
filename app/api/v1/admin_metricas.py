from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.servicio import Servicio
from app.models.cotizacion import Cotizacion
from app.models.usuario import Usuario
from app.core.dependencies import require_permission

router = APIRouter(prefix="/admin/metrics", tags=["Admin Métricas"])

@router.get("/dashboard", dependencies=[Depends(require_permission("dashboard:view"))])
def get_dashboard_metrics(db: Session = Depends(get_db)):
    total_servicios = db.query(func.count(Servicio.id)).scalar() or 0
    servicios_activos = db.query(func.count(Servicio.id)).filter(Servicio.activo == True).scalar() or 0
    servicios_destacados = db.query(func.count(Servicio.id)).filter(Servicio.destacado == True).scalar() or 0

    total_cotizaciones = db.query(func.count(Cotizacion.id)).scalar() or 0
    cotizaciones_pendientes = db.query(func.count(Cotizacion.id)).filter(Cotizacion.estado == "Pendiente").scalar() or 0
    cotizaciones_contactadas = db.query(func.count(Cotizacion.id)).filter(Cotizacion.estado == "Contactado").scalar() or 0
    cotizaciones_confirmadas = db.query(func.count(Cotizacion.id)).filter(Cotizacion.estado == "Confirmada").scalar() or 0

    volumen_estimado_bob = db.query(func.sum(Cotizacion.total_estimado)).scalar() or 0.0

    total_usuarios = db.query(func.count(Usuario.id)).scalar() or 0

    # Últimas 5 cotizaciones para atención inmediata
    recientes = db.query(Cotizacion).order_by(Cotizacion.timestamp.desc()).limit(5).all()
    recientes_data = [
        {
            "id": c.id,
            "codigo": c.codigo_seguimiento or f"RXS-{c.id}",
            "cliente": c.nombre,
            "telefono": c.telefono,
            "paquete": c.paquete,
            "total_bob": float(c.total_estimado or 0),
            "estado": c.estado,
            "fecha": c.fecha_evento.isoformat()
        }
        for c in recientes
    ]

    return {
        "catalogo": {
            "total": total_servicios,
            "activos": servicios_activos,
            "destacados": servicios_destacados
        },
        "cotizaciones": {
            "total": total_cotizaciones,
            "pendientes": cotizaciones_pendientes,
            "contactadas": cotizaciones_contactadas,
            "confirmadas": cotizaciones_confirmadas,
            "volumen_estimado_bob": float(volumen_estimado_bob)
        },
        "usuarios": {
            "total": total_usuarios
        },
        "ultimas_solicitudes": recientes_data
    }
