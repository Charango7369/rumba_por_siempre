from typing import Callable, List
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.utils.security import decode_token

security_bearer = HTTPBearer(auto_error=True)

def get_client_ip(request: Request) -> str:
    """Extrae la IP real del cliente detrás de proxies de Railway o Cloudflare."""
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> Usuario:
    token = credentials.credentials
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo de token no autorizado para esta operación."
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token no contiene identidad válida."
        )

    usuario = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if not usuario or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario no existe o se encuentra desactivado."
        )

    return usuario

def require_role(allowed_roles: List[str]) -> Callable:
    """Valida que el usuario tenga al menos uno de los roles permitidos."""
    def dependency(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        user_roles = [r.codigo for r in usuario.roles]
        if usuario.rol and usuario.rol not in user_roles:
            user_roles.append(usuario.rol)

        # SuperAdministrador tiene acceso irrestricto
        if "superadmin" in user_roles:
            return usuario

        if not any(role in allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: se requiere uno de los roles: {allowed_roles}"
            )
        return usuario
    return dependency

def require_permission(permission_code: str) -> Callable:
    """Valida permiso granular específico del usuario o bypass de superadmin."""
    def dependency(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        user_roles = [r.codigo for r in usuario.roles]
        if usuario.rol and usuario.rol not in user_roles:
            user_roles.append(usuario.rol)

        if "superadmin" in user_roles:
            return usuario

        # Recolectar todos los códigos de permisos de los roles del usuario
        permisos_usuario = set()
        for r in usuario.roles:
            for p in r.permisos:
                permisos_usuario.add(p.codigo)

        # Mapeo de compatibilidad con roles simples
        if "admin" in user_roles and not permission_code.startswith("users:"):
            permisos_usuario.add(permission_code)

        if permission_code not in permisos_usuario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: permiso '{permission_code}' requerido."
            )
        return usuario
    return dependency
