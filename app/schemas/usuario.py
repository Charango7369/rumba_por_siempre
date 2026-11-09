from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.rbac import RolResponse

class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    activo: bool = True

class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=6, max_length=100)
    roles_codigos: List[str] = Field(default_factory=lambda: ["comercial"])

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=120)
    email: Optional[EmailStr] = None
    activo: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    roles_codigos: Optional[List[str]] = None

class UsuarioResponse(UsuarioBase):
    id: int
    ultimo_acceso: Optional[datetime] = None
    creado_en: datetime
    roles: List[RolResponse] = []

    model_config = ConfigDict(from_attributes=True)
