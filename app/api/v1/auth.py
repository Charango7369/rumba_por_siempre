from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest, UserMeResponse
from app.schemas.usuario import UsuarioResponse
from app.schemas.rbac import RolResponse, PermisoResponse
from app.services.auth_service import autenticar_usuario, generar_par_tokens, refrescar_access_token, revocar_refresh_token
from app.core.dependencies import get_current_user, get_client_ip
from app.services.auditoria_service import registrar_auditoria

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    usuario = autenticar_usuario(db, payload)
    access_token, refresh_token, permisos = generar_par_tokens(db, usuario)

    # Auditoría de inicio de sesión exitoso
    registrar_auditoria(
        db=db,
        usuario=usuario,
        accion="LOGIN_EXITOSO",
        recurso="auth",
        recurso_id=str(usuario.id),
        ip=get_client_ip(request),
        user_agent=request.headers.get("user-agent")
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        usuario=usuario,
        permisos=permisos
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    access_token, new_refresh_token, permisos = refrescar_access_token(db, payload.refresh_token)
    from app.utils.security import decode_token
    t_payload = decode_token(access_token)
    user_id = int(t_payload.get("sub"))
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        usuario=usuario,
        permisos=permisos
    )

@router.get("/me", response_model=UserMeResponse)
def get_mi_perfil(usuario: Usuario = Depends(get_current_user)):
    user_roles = [r.codigo for r in usuario.roles]
    if usuario.rol and usuario.rol not in user_roles:
        user_roles.append(usuario.rol)

    permisos = set()
    if "superadmin" in user_roles:
        permisos.add("*")
    for r in usuario.roles:
        for p in r.permisos:
            permisos.add(p.codigo)

    return UserMeResponse(
        usuario=usuario,
        roles=user_roles,
        permisos=sorted(list(permisos))
    )

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(payload: RefreshTokenRequest, request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    revocar_refresh_token(db, payload.refresh_token)
    registrar_auditoria(
        db=db,
        usuario=usuario,
        accion="LOGOUT",
        recurso="auth",
        recurso_id=str(usuario.id),
        ip=get_client_ip(request),
        user_agent=request.headers.get("user-agent")
    )
    return {"message": "Sesión finalizada exitosamente."}
