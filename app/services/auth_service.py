from datetime import datetime, timezone
import hashlib
from typing import Tuple, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.usuario import Usuario
from app.models.refresh_token import RefreshToken
from app.schemas.auth import LoginRequest, TokenResponse
from app.utils.security import verify_password, create_access_token, create_refresh_token, decode_token

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def autenticar_usuario(db: Session, credenciales: LoginRequest) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.email == credenciales.email).first()
    if not usuario or not verify_password(credenciales.password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de acceso incorrectas."
        )
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta se encuentra inactiva. Contacta al administrador."
        )

    usuario.ultimo_acceso = datetime.now(timezone.utc)
    db.commit()
    db.refresh(usuario)
    return usuario

def generar_par_tokens(db: Session, usuario: Usuario) -> Tuple[str, str, List[str]]:
    # Obtener permisos consolidados
    user_roles = [r.codigo for r in usuario.roles]
    if usuario.rol and usuario.rol not in user_roles:
        user_roles.append(usuario.rol)

    permisos = set()
    if "superadmin" in user_roles:
        permisos.add("*")  # Permiso total
    for r in usuario.roles:
        for p in r.permisos:
            permisos.add(p.codigo)

    permisos_lista = sorted(list(permisos))

    access_token = create_access_token({
        "sub": str(usuario.id),
        "email": usuario.email,
        "nombre": usuario.nombre,
        "roles": user_roles,
        "permisos": permisos_lista
    })

    refresh_token_jwt, expire_dt = create_refresh_token(subject=str(usuario.id))

    # Guardar en base de datos para control de revocación
    rt_record = RefreshToken(
        usuario_id=usuario.id,
        token_hash=hash_token(refresh_token_jwt),
        fecha_expiracion=expire_dt,
        revocado=False
    )
    db.add(rt_record)
    db.commit()

    return access_token, refresh_token_jwt, permisos_lista

def refrescar_access_token(db: Session, refresh_token_jwt: str) -> Tuple[str, str, List[str]]:
    payload = decode_token(refresh_token_jwt)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no es de tipo refresh.")

    user_id = payload.get("sub")
    t_hash = hash_token(refresh_token_jwt)

    rt_record = db.query(RefreshToken).filter(
        RefreshToken.token_hash == t_hash,
        RefreshToken.revocado == False
    ).first()

    if not rt_record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh Token inválido o revocado.")

    # Invalidar el token anterior (rotación de refresh tokens)
    rt_record.revocado = True
    db.commit()

    usuario = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo o no existe.")

    return generar_par_tokens(db, usuario)

def revocar_refresh_token(db: Session, refresh_token_jwt: str) -> bool:
    try:
        t_hash = hash_token(refresh_token_jwt)
        rt_record = db.query(RefreshToken).filter(RefreshToken.token_hash == t_hash).first()
        if rt_record:
            rt_record.revocado = True
            db.commit()
            return True
    except Exception:
        pass
    return False
