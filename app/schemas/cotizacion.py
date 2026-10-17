"""Contrato de /api/cotizacion (Pydantic v2). Conserva los límites y precios que ya tenías."""
import re
from datetime import date, datetime, timedelta, timezone
from typing import List

from pydantic import AliasChoices, BaseModel, Field, field_validator

# False = comportamiento actual (paquete desconocido -> premium; extras desconocidos suman 0).
# True  = responde 422 si el paquete/extra no existe. Actívalo cuando confirmes que el form envía solo claves válidas.
CATALOGO_ESTRICTO = False

BASE_PRICES = {"esencial": 1800, "premium": 3200, "pro": 5200}
EXTRA_PRICES = {"pantallas": 900, "humo": 350, "animacion": 600, "streaming": 800}

_CTRL = re.compile(r"[\x00-\x1f\x7f]")
_SPACES = re.compile(r"\s+")
_TEL_SEP = re.compile(r"[\s().\-]")
_TEL_OK = re.compile(r"^\+?\d{6,15}$")
_BOLIVIA = timezone(timedelta(hours=-4))  # sin horario de verano


def _texto(v: str) -> str:
    """Quita caracteres de control y colapsa espacios. No escapa HTML: React y quote() ya codifican la salida."""
    return _SPACES.sub(" ", _CTRL.sub("", v)).strip()


class CotizacionRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    telefono: str = Field(min_length=6, max_length=24)
    ciudad: str = Field(min_length=2, max_length=80)
    # Acepta "fecha_evento" (nuevo) y "fecha" (el nombre que usa hoy el frontend).
    fecha_evento: date = Field(validation_alias=AliasChoices("fecha_evento", "fecha"))
    tipo_evento: str = Field(min_length=2, max_length=60)
    invitados: int = Field(ge=20, le=5000)
    paquete: str = Field(min_length=2, max_length=40)
    extras: List[str] = Field(default_factory=list, max_length=10)

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
            raise ValueError("Teléfono inválido: 6 a 15 dígitos, con + opcional al inicio")
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
        v = _texto(v).lower()
        if CATALOGO_ESTRICTO and v not in BASE_PRICES:
            raise ValueError(f"Paquete no válido. Opciones: {', '.join(BASE_PRICES)}")
        return v

    @field_validator("extras")
    @classmethod
    def _extras(cls, v: List[str]) -> List[str]:
        out = []
        for x in v:
            x = _texto(x)[:50].lower()
            if not x or x in out:
                continue
            if CATALOGO_ESTRICTO and x not in EXTRA_PRICES:
                raise ValueError(f"Extra no válido: {x}")
            out.append(x)
        return out
