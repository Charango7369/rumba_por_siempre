import math
import random
from datetime import datetime
from typing import Tuple, Dict, Any, Optional
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from app.models.servicio import Servicio
from app.models.cotizacion import Cotizacion
from app.models.configuracion import Configuracion
from app.schemas.cotizacion import CotizacionRequest

def generar_codigo_seguimiento(db: Session) -> str:
    """Genera un código único anual como RXS-2026-1042."""
    anio = datetime.now().year
    for _ in range(10):
        aleatorio = random.randint(1000, 9999)
        codigo = f"RXS-{anio}-{aleatorio}"
        existe = db.query(Cotizacion).filter(Cotizacion.codigo_seguimiento == codigo).first()
        if not existe:
            return codigo
    return f"RXS-{anio}-{int(datetime.now().timestamp())}"

def obtener_parametro_float(db: Session, clave: str, default: float) -> float:
    conf = db.query(Configuracion).filter(Configuracion.clave == clave).first()
    if conf:
        try:
            return float(conf.valor)
        except ValueError:
            pass
    return default

def obtener_parametro_int(db: Session, clave: str, default: int) -> int:
    conf = db.query(Configuracion).filter(Configuracion.clave == clave).first()
    if conf:
        try:
            return int(conf.valor)
        except ValueError:
            pass
    return default

def calcular_cotizacion_dinamica(
    payload: CotizacionRequest,
    db: Session
) -> Tuple[float, Dict[str, Any], Optional[Servicio]]:
    """
    Calcula el costo total consultando los precios vigentes en la Base de Datos.
    Cero precios hardcodeados en el código.
    """
    # 1. Obtener paquete principal por slug o por nombre
    paquete_query = payload.paquete.strip()
    servicio = db.query(Servicio).filter(
        (Servicio.slug == paquete_query.lower()) | (Servicio.nombre.ilike(paquete_query)),
        Servicio.activo == True
    ).first()

    # Si no coincide exactamente, buscar servicio por defecto
    if not servicio:
        servicio = db.query(Servicio).filter(Servicio.activo == True).order_by(Servicio.orden_visualizacion).first()

    precio_paquete = 0.0
    nombre_paquete = payload.paquete
    servicio_id = None

    if servicio:
        servicio_id = servicio.id
        nombre_paquete = servicio.nombre
        precio_paquete = float(servicio.precio_promocional if (servicio.precio_promocional and servicio.precio_promocional > 0) else servicio.precio_base)

    # 2. Parámetros de capacidad (leídos de configuración dinámica o defaults de negocio)
    capacidad_base = obtener_parametro_int(db, "CAPACIDAD_BASE_INVITADOS", 150)
    bloque_invitados = obtener_parametro_int(db, "TAMANO_BLOQUE_INVITADOS", 50)
    costo_por_bloque = obtener_parametro_float(db, "COSTO_POR_BLOQUE_INVITADOS", 180.0)

    costo_capacidad = 0.0
    if payload.invitados > capacidad_base:
        bloques = math.ceil((payload.invitados - capacidad_base) / bloque_invitados)
        costo_capacidad = float(bloques * costo_por_bloque)

    # 3. Extras dinámicos consultados desde la tabla Servicios (es_extra == True)
    costo_extras = 0.0
    detalles_extras = []

    if payload.extras:
        slugs_normalizados = [x.strip().lower() for x in payload.extras]
        extras_db = db.query(Servicio).filter(
            Servicio.slug.in_(slugs_normalizados),
            Servicio.activo == True
        ).all()

        for ext in extras_db:
            precio_ext = float(ext.precio_promocional if (ext.precio_promocional and ext.precio_promocional > 0) else ext.precio_base)
            costo_extras += precio_ext
            detalles_extras.append({
                "slug": ext.slug,
                "nombre": ext.nombre,
                "precio": precio_ext
            })

    total = precio_paquete + costo_capacidad + costo_extras

    desglose = {
        "paquete": {
            "nombre": nombre_paquete,
            "servicio_id": servicio_id,
            "precio_unitario": precio_paquete
        },
        "capacidad": {
            "invitados_totales": payload.invitados,
            "invitados_base_incluidos": capacidad_base,
            "costo_adicional": costo_capacidad
        },
        "extras": detalles_extras,
        "costo_extras_total": costo_extras,
        "moneda": "BOB",
        "total_estimado": round(total, 2)
    }

    return total, desglose, servicio
