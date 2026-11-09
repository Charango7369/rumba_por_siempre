from pydantic import BaseModel, EmailStr
from typing import List, Optional
from app.schemas.usuario import UsuarioResponse

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse
    permisos: List[str]

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserMeResponse(BaseModel):
    usuario: UsuarioResponse
    roles: List[str]
    permisos: List[str]
