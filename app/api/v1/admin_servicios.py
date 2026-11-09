import os
import uuid
import re
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.servicio import Servicio
from app.models.usuario import Usuario
from app.schemas.servicio import (
    ServicioResponse, ServicioCreate, ServicioUpdate, ServicioPriceUpdate, ServicioStatusUpdate
)
from app.core.dependencies import require_permission, get_client_ip
from app.services.auditoria_service import registrar_auditoria

router = APIRouter(prefix="/admin/services", tags=["Admin Catálogo"])

UPLOAD_DIR = os.path.join("static", "uploads", "servicios")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

@router.post("/upload-image", dependencies=[Depends(require_permission("catalog:update"))])
async def upload_servicio_imagen(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("catalog:update"))
):
    """
    Sube una imagen al servidor para ser utilizada como portada o en la galería.
    Valida tamaño (máx 5MB), formatos seguros (JPG, PNG, WEBP) y genera un nombre único.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS or file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato no permitido. Se aceptan únicamente imágenes JPG, PNG o WEBP. Recibido: {file.content_type}"
        )

    # Sanitizar nombre del archivo
    nombre_limpio = re.sub(r"[^a-zA-Z0-9_.-]", "", file.filename)
    nombre_final = f"{uuid.uuid4().hex[:10]}_{nombre_limpio}"
    destino = os.path.join(UPLOAD_DIR, nombre_final)

    # Leer y validar tamaño
    contenido = await file.read()
    if len(contenido) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La imagen excede el límite máximo permitido de 5 MB."
        )

    with open(destino, "wb") as f:
        f.write(contenido)

    url_relativa = f"/static/uploads/servicios/{nombre_final}"

    registrar_auditoria(
        db=db,
        usuario=usuario,
        accion="SUBIR_IMAGEN",
        recurso="servicios_media",
        recurso_id=nombre_final,
        ip=get_client_ip(request),
        valores_nuevos={"archivo": nombre_final, "peso_bytes": len(contenido), "url": url_relativa},
        user_agent=request.headers.get("user-agent")
    )

    return {
        "url": url_relativa,
        "filename": nombre_final,
        "size_bytes": len(contenido),
        "content_type": file.content_type,
        "message": "Imagen subida exitosamente"
    }

@router.get("", response_model=List[ServicioResponse], dependencies=[Depends(require_permission("catalog:read"))])
def admin_listar_servicios(
    db: Session = Depends(get_db),
    categoria: Optional[str] = None,
    activo: Optional[bool] = None
):
    query = db.query(Servicio)
    if categoria:
        query = query.filter(Servicio.categoria.ilike(categoria.strip()))
    if activo is not None:
        query = query.filter(Servicio.activo == activo)

    return query.order_by(Servicio.orden_visualizacion.asc(), Servicio.id.desc()).all()

@router.post("", response_model=ServicioResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("catalog:create"))])
def admin_crear_servicio(
    payload: ServicioCreate,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("catalog:create"))
):
    # Verificar unicidad de slug
    slug_limpio = payload.slug.strip().lower()
    existe = db.query(Servicio).filter(Servicio.slug == slug_limpio).first()
    if existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un servicio con el slug '{slug_limpio}'."
        )

    nuevo_servicio = Servicio(
        nombre=payload.nombre,
        slug=slug_limpio,
        categoria=payload.categoria,
        descripcion_corta=payload.descripcion_corta,
        descripcion_larga=payload.descripcion_larga,
        precio_base=payload.precio_base,
        precio_promocional=payload.precio_promocional,
        imagen_principal=payload.imagen_principal,
        galeria_imagenes=payload.galeria_imagenes,
        especificaciones_tecnicas=payload.especificaciones_tecnicas,
        es_extra=payload.es_extra,
        activo=payload.activo,
        destacado=payload.destacado,
        orden_visualizacion=payload.orden_visualizacion
    )
    db.add(nuevo_servicio)
    db.commit()
    db.refresh(nuevo_servicio)

    registrar_auditoria(
        db=db,
        usuario=usuario,
        accion="CREAR_SERVICIO",
        recurso="servicios",
        recurso_id=str(nuevo_servicio.id),
        ip=get_client_ip(request),
        valores_nuevos={"nombre": nuevo_servicio.nombre, "slug": nuevo_servicio.slug, "precio_base": float(nuevo_servicio.precio_base)},
        user_agent=request.headers.get("user-agent")
    )

    return nuevo_servicio

@router.put("/{service_id}", response_model=ServicioResponse, dependencies=[Depends(require_permission("catalog:update"))])
def admin_actualizar_servicio_completo(
    service_id: int,
    payload: ServicioCreate,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("catalog:update"))
):
    servicio = db.query(Servicio).filter(Servicio.id == service_id).first()
    if not servicio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio no encontrado.")

    slug_limpio = payload.slug.strip().lower()
    if slug_limpio != servicio.slug:
        existe = db.query(Servicio).filter(Servicio.slug == slug_limpio, Servicio.id != service_id).first()
        if existe:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El slug ya pertenece a otro servicio.")

    previos = {
        "nombre": servicio.nombre,
        "precio_base": float(servicio.precio_base),
        "precio_promocional": float(servicio.precio_promocional) if servicio.precio_promocional else None,
        "activo": servicio.activo
    }

    for campo, valor in payload.model_dump().items():
        setattr(servicio, campo, valor)

    db.commit()
    db.refresh(servicio)

    registrar_auditoria(
        db=db,
        usuario=usuario,
        accion="EDITAR_SERVICIO_COMPLETO",
        recurso="servicios",
        recurso_id=str(servicio.id),
        ip=get_client_ip(request),
        valores_previos=previos,
        valores_nuevos={"nombre": servicio.nombre, "precio_base": float(servicio.precio_base), "activo": servicio.activo},
        user_agent=request.headers.get("user-agent")
    )

    return servicio

@router.patch("/{service_id}", response_model=ServicioResponse, dependencies=[Depends(require_permission("catalog:update"))])
def admin_actualizar_servicio_parcial(
    service_id: int,
    payload: ServicioUpdate,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("catalog:update"))
):
    servicio = db.query(Servicio).filter(Servicio.id == service_id).first()
    if not servicio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio no encontrado.")

    datos = payload.model_dump(exclude_unset=True)
    previos = {k: getattr(servicio, k) for k in datos.keys() if hasattr(servicio, k)}

    for campo, valor in datos.items():
        setattr(servicio, campo, valor)

    db.commit()
    db.refresh(servicio)

    registrar_auditoria(
        db=db,
        usuario=usuario,
        accion="MODIFICACION_PARCIAL_SERVICIO",
        recurso="servicios",
        recurso_id=str(servicio.id),
        ip=get_client_ip(request),
        valores_previos={k: str(v) for k, v in previos.items()},
        valores_nuevos={k: str(v) for k, v in datos.items()},
        user_agent=request.headers.get("user-agent")
    )

    return servicio

@router.patch("/{service_id}/price", dependencies=[Depends(require_permission("catalog:pricing"))])
def admin_modificar_precios(
    service_id: int,
    payload: ServicioPriceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("catalog:pricing"))
):
    servicio = db.query(Servicio).filter(Servicio.id == service_id).first()
    if not servicio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio no encontrado.")

    previos = {
        "precio_base": float(servicio.precio_base),
        "precio_promocional": float(servicio.precio_promocional) if servicio.precio_promocional else None
    }

    servicio.precio_base = payload.precio_base
    servicio.precio_promocional = payload.precio_promocional
    db.commit()
    db.refresh(servicio)

    nuevos = {
        "precio_base": float(servicio.precio_base),
        "precio_promocional": float(servicio.precio_promocional) if servicio.precio_promocional else None
    }

    registrar_auditoria(
        db=db,
        usuario=usuario,
        accion="CAMBIO_PRECIO",
        recurso="servicios",
        recurso_id=str(servicio.id),
        ip=get_client_ip(request),
        valores_previos=previos,
        valores_nuevos=nuevos,
        user_agent=request.headers.get("user-agent")
    )

    return {"message": "Precios actualizados exitosamente", "servicio_id": servicio.id, "precios": nuevos}

@router.patch("/{service_id}/status", dependencies=[Depends(require_permission("catalog:toggle"))])
def admin_toggle_estado_servicio(
    service_id: int,
    payload: ServicioStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("catalog:toggle"))
):
    servicio = db.query(Servicio).filter(Servicio.id == service_id).first()
    if not servicio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio no encontrado.")

    estado_anterior = servicio.activo
    servicio.activo = payload.activo
    db.commit()

    registrar_auditoria(
        db=db,
        usuario=usuario,
        accion="CAMBIO_ESTADO_ACTIVACION",
        recurso="servicios",
        recurso_id=str(servicio.id),
        ip=get_client_ip(request),
        valores_previos={"activo": estado_anterior},
        valores_nuevos={"activo": servicio.activo},
        user_agent=request.headers.get("user-agent")
    )

    return {"message": f"Servicio {'activado' if servicio.activo else 'desactivado'}", "activo": servicio.activo}

@router.delete("/{service_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(require_permission("catalog:delete"))])
def admin_eliminar_servicio(
    service_id: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("catalog:delete"))
):
    servicio = db.query(Servicio).filter(Servicio.id == service_id).first()
    if not servicio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio no encontrado.")

    nombre_servicio = servicio.nombre
    db.delete(servicio)
    db.commit()

    registrar_auditoria(
        db=db,
        usuario=usuario,
        accion="ELIMINAR_SERVICIO",
        recurso="servicios",
        recurso_id=str(service_id),
        ip=get_client_ip(request),
        valores_previos={"nombre": nombre_servicio},
        user_agent=request.headers.get("user-agent")
    )

    return {"message": f"Servicio '{nombre_servicio}' eliminado definitivamente."}
