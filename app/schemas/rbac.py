from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class PermisoResponse(BaseModel):
    id: int
    codigo: str
    modulo: str
    descripcion: str

    model_config = ConfigDict(from_attributes=True)

class RolBase(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    es_sistema: bool = False

class RolResponse(RolBase):
    id: int
    permisos: List[PermisoResponse] = []

    model_config = ConfigDict(from_attributes=True)

class RolUpdatePermisos(BaseModel):
    permisos_codigos: List[str]
