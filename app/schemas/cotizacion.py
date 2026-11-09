"""Contrato de /api/cotizacion y /api/v1/quotes (Pydantic v2).
Elimina precios hardcodeados y delega el cálculo al catálogo de base de datos.
"""
import re
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

_CTRL = re.compile(r"[\x00-\x1f\x7f]")
_SPACES = re.compile(r"\s+")
_TEL_SEP = re.compile(r"[\s().\-]")
_TEL_OK = re.compile(r"^\+?\d{6,15}$")
_BOLIVIA = timezone(timedelta(hours=-4))  # Hora Boliviana (UTC-4)

def _texto(v: str) -> str:
    """Quita caracteres de control y colapsa espacios."""
    return _SPACES.sub(" ", _CTRL.sub("", v)).strip()

class CotizacionRequest(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    telefono: str = Field(..., min_length=6, max_length=25)
    ciudad: str = Field(..., min_length=2, max_length=80)
    # Acepta "fecha_evento" y "fecha" (retrocompatibilidad con el frontend)
    fecha_evento: date = Field(..., validation_alias=AliasChoices("fecha_evento", "fecha"))
    tipo_evento: str = Field(..., min_length=2, max_length=60)
    invitados: int = Field(..., ge=20, le=5000)
    paquete: str = Field(..., min_length=2, max_length=80)
    extras: List[str] = Field(default_factory=list, max_length=15)

    @field_validator("nombre", "ciudad", "tipo_evento")
    @classmethod
    def _limpiar(cls, v: str) -> str:
        v = _texto(v)
        if len(v) < 2:
            raise ValueError("Texto demasiado corto")
        return v

    @field_validator("telefono")
    @classmethod
    def _tel(cls, v: str) -> str:
        v = _TEL_SEP.sub("", v)
        if not _TEL_OK.match(v):
            raise ValueError("Teléfono inválido: 6 a 15 dígitos")
        return v

    @field_validator("fecha_evento")
    @classmethod
    def _fecha(cls, v: date) -> date:
        hoy = datetime.now(_BOLIVIA).date()
        if v < hoy:
            raise ValueError("La fecha del evento no puede ser anterior a hoy")
        if (v - hoy).days > 365 * 3:
            raise ValueError("La fecha no puede superar los 3 años")
        return v

    @field_validator("paquete")
    @classmethod
    def _paquete(cls, v: str) -> str:
        return _texto(v)

    @field_validator("extras")
    @classmethod
    def _extras(cls, v: List[str]) -> List[str]:
        out = []
        for x in v:
            x = _texto(x)[:50]
            if x and x not in out:
                out.append(x)
        return out

class CotizacionStatusUpdate(BaseModel):
    estado: str = Field(..., description="Pendiente, Contactado, En Negociacion, Confirmada, Cancelada")
    observaciones: Optional[str] = None

class CotizacionResponse(BaseModel):
    id: int
    codigo_seguimiento: Optional[str] = None
    nombre: str
    telefono: str
    ciudad: str
    fecha_evento: date
    tipo_evento: str
    invitados: int
    paquete: str
    extras: List[Any]
    total_estimado: Optional[float] = None
    desglose_calculo: Optional[Dict[str, Any]] = None
    estado: str
    observaciones: Optional[str] = None
    timestamp: datetime
    actualizado_en: datetime

    model_config = ConfigDict(from_attributes=True)
