from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class ServicioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    slug: str = Field(..., min_length=2, max_length=120)
    categoria: str = Field(..., min_length=2, max_length=60)
    descripcion_corta: Optional[str] = Field(None, max_length=255)
    descripcion_larga: Optional[str] = None
    precio_base: Decimal = Field(..., ge=0)
    precio_promocional: Optional[Decimal] = Field(None, ge=0)
    imagen_principal: str = Field(..., max_length=500)
    galeria_imagenes: List[str] = Field(default_factory=list)
    especificaciones_tecnicas: List[str] = Field(default_factory=list)
    es_extra: bool = False
    activo: bool = True
    destacado: bool = False
    orden_visualizacion: int = 0

class ServicioCreate(ServicioBase):
    pass

class ServicioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=120)
    slug: Optional[str] = Field(None, min_length=2, max_length=120)
    categoria: Optional[str] = Field(None, min_length=2, max_length=60)
    descripcion_corta: Optional[str] = None
    descripcion_larga: Optional[str] = None
    precio_base: Optional[Decimal] = Field(None, ge=0)
    precio_promocional: Optional[Decimal] = Field(None, ge=0)
    imagen_principal: Optional[str] = None
    galeria_imagenes: Optional[List[str]] = None
    especificaciones_tecnicas: Optional[List[str]] = None
    es_extra: Optional[bool] = None
    activo: Optional[bool] = None
    destacado: Optional[bool] = None
    orden_visualizacion: Optional[int] = None

class ServicioPriceUpdate(BaseModel):
    precio_base: Decimal = Field(..., ge=0)
    precio_promocional: Optional[Decimal] = Field(None, ge=0)

class ServicioStatusUpdate(BaseModel):
    activo: bool

class ServicioResponse(ServicioBase):
    id: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    model_config = ConfigDict(from_attributes=True)

class OpcionCotizacionResponse(BaseModel):
    paquetes: List[ServicioResponse]
    extras: List[ServicioResponse]
