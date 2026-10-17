"""Traduce los errores de validación de Pydantic/FastAPI a mensajes en español, por campo."""
from typing import Dict, List

_ETIQUETAS = {
    "nombre": "El nombre", "telefono": "El teléfono", "ciudad": "La ciudad",
    "fecha": "La fecha", "fecha_evento": "La fecha", "tipo_evento": "El tipo de evento",
    "invitados": "Los invitados", "paquete": "El paquete", "extras": "Los extras",
}


def _mensaje(campo: str, tipo: str, msg: str, ctx: dict) -> str:
    et = _ETIQUETAS.get(campo, "El valor")
    if tipo == "missing":
        return "Este campo es obligatorio"
    if tipo == "string_too_short":
        return f"{et} debe tener al menos {ctx.get('min_length')} caracteres"
    if tipo == "string_too_long":
        return f"{et} no puede superar {ctx.get('max_length')} caracteres"
    if tipo == "too_long":
        return f"{et}: máximo {ctx.get('max_length')} elementos"
    if tipo in ("greater_than_equal", "greater_than"):
        n = ctx.get("ge", ctx.get("gt"))
        return f"Debe haber al menos {n} invitados" if campo == "invitados" else f"{et} debe ser como mínimo {n}"
    if tipo in ("less_than_equal", "less_than"):
        n = ctx.get("le", ctx.get("lt"))
        return f"El máximo es {n} invitados" if campo == "invitados" else f"{et} debe ser como máximo {n}"
    if tipo in ("int_parsing", "int_type", "int_from_float"):
        return f"{et} debe ser un número entero"
    if tipo.startswith("date") or tipo == "datetime_parsing":
        return "Fecha inválida (formato AAAA-MM-DD)"
    if tipo == "string_type":
        return f"{et} debe ser texto"
    if tipo == "json_invalid":
        return "El cuerpo de la petición no es un JSON válido"
    if tipo == "value_error":
        return msg.removeprefix("Value error, ")  # ya vienen en español desde los validadores
    return msg


def traducir_errores(errores: List[dict]) -> Dict[str, str]:
    """{campo: mensaje}. Si un campo falla varias veces, se conserva el primer mensaje."""
    out: Dict[str, str] = {}
    for e in errores:
        loc = e.get("loc", ())
        campo = str(loc[1]) if len(loc) > 1 else (str(loc[-1]) if loc else "cuerpo")
        out.setdefault(campo, _mensaje(campo, e.get("type", ""), e.get("msg", ""), e.get("ctx") or {}))
    return out
