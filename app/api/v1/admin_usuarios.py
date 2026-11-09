from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.rbac import Rol
from app.schemas.usuario import UsuarioResponse, UsuarioCreate, UsuarioUpdate
from app.utils.security import get_password_hash
from app.core.dependencies import require_role, get_client_ip
from app.services.auditoria_service import registrar_auditoria

router = APIRouter(prefix="/admin/users", tags=["Admin Usuarios (SuperAdmin)"])

@router.get("", response_model=List[UsuarioResponse], dependencies=[Depends(require_role(["superadmin"]))])
def admin_listar_usuarios(db: Session = Depends(get_db)):
    return db.query(Usuario).order_by(Usuario.id.asc()).all()

@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(["superadmin"]))])
def admin_crear_usuario(
    payload: UsuarioCreate,
    request: Request,
    db: Session = Depends(get_db),
    superadmin: Usuario = Depends(require_role(["superadmin"]))
):
    existe = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if existe:
        raise HTTPException(status_code=400, detail="Ya existe un usuario con este correo electrónico.")

    nuevo_user = Usuario(
        nombre=payload.nombre,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        activo=payload.activo,
        rol=payload.roles_codigos[0] if payload.roles_codigos else "comercial"
    )

    # Asignar roles relacionales
    if payload.roles_codigos:
        roles_db = db.query(Rol).filter(Rol.codigo.in_(payload.roles_codigos)).all()
        nuevo_user.roles = roles_db

    db.add(nuevo_user)
    db.commit()
    db.refresh(nuevo_user)

    registrar_auditoria(
        db=db,
        usuario=superadmin,
        accion="CREAR_USUARIO",
        recurso="usuarios",
        recurso_id=str(nuevo_user.id),
        ip=get_client_ip(request),
        valores_nuevos={"nombre": nuevo_user.nombre, "email": nuevo_user.email, "roles": payload.roles_codigos},
        user_agent=request.headers.get("user-agent")
    )

    return nuevo_user

@router.patch("/{user_id}", response_model=UsuarioResponse, dependencies=[Depends(require_role(["superadmin"]))])
def admin_actualizar_usuario(
    user_id: int,
    payload: UsuarioUpdate,
    request: Request,
    db: Session = Depends(get_db),
    superadmin: Usuario = Depends(require_role(["superadmin"]))
):
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if payload.nombre is not None:
        usuario.nombre = payload.nombre
    if payload.email is not None:
        usuario.email = payload.email
    if payload.activo is not None:
        usuario.activo = payload.activo
    if payload.password:
        usuario.hashed_password = get_password_hash(payload.password)
    if payload.roles_codigos is not None:
        roles_db = db.query(Rol).filter(Rol.codigo.in_(payload.roles_codigos)).all()
        usuario.roles = roles_db
        if payload.roles_codigos:
            usuario.rol = payload.roles_codigos[0]

    db.commit()
    db.refresh(usuario)

    registrar_auditoria(
        db=db,
        usuario=superadmin,
        accion="EDITAR_USUARIO",
        recurso="usuarios",
        recurso_id=str(usuario.id),
        ip=get_client_ip(request),
        valores_nuevos={"nombre": usuario.nombre, "email": usuario.email, "activo": usuario.activo},
        user_agent=request.headers.get("user-agent")
    )

    return usuario

@router.delete("/{user_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(require_role(["superadmin"]))])
def admin_eliminar_usuario(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    superadmin: Usuario = Depends(require_role(["superadmin"]))
):
    if user_id == superadmin.id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta de SuperAdministrador.")

    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    email_del = usuario.email
    db.delete(usuario)
    db.commit()

    registrar_auditoria(
        db=db,
        usuario=superadmin,
        accion="ELIMINAR_USUARIO",
        recurso="usuarios",
        recurso_id=str(user_id),
        ip=get_client_ip(request),
        valores_previos={"email": email_del},
        user_agent=request.headers.get("user-agent")
    )

    return {"message": f"Usuario '{email_del}' eliminado."}
