from pydantic import BaseModel, ConfigDict
from typing import Optional

# 1. Esquema base con los campos comunes
class ServicioBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio_base: float
    categoria: Optional[str] = None
    disponible: bool = True

# 2. Esquema para crear un servicio (si en el futuro haces un POST /servicios)
class ServicioCreate(ServicioBase):
    pass

# 3. Esquema de respuesta para el frontend (incluye el ID generado por la BD)
class ServicioResponse(ServicioBase):
    id: int

    # Le indica a Pydantic que lea los datos directamente del objeto SQLAlchemy
    model_config = ConfigDict(from_attributes=True)