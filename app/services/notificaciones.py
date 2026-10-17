"""Avisos de nueva cotización: correo al admin, WhatsApp opcional y listeners (p. ej. WebSocket).
Se ejecuta en segundo plano y nunca propaga errores al endpoint."""
import asyncio
import inspect
import logging
import os
import smtplib
from email.message import EmailMessage
from typing import Awaitable, Callable, Dict, List, Union

import httpx

log = logging.getLogger("cotizaciones.notif")
Listener = Callable[[Dict], Union[None, Awaitable[None]]]
_listeners: List[Listener] = []


def register_listener(fn: Listener) -> None:
    """Conecta tu WebSocket sin tocarlo: register_listener(lambda c: manager.broadcast({"type": "nueva_cotizacion", "data": c}))"""
    _listeners.append(fn)


def _resumen(c: Dict) -> str:
    extras = ", ".join(c["extras"]) or "sin extras"
    return (
        f"Nueva cotización #{c.get('id') or 's/n'}\n"
        f"Cliente: {c['nombre']} ({c['telefono']})\n"
        f"Ciudad: {c['ciudad']}\n"
        f"Evento: {c['tipo_evento']} el {c['fecha']} · {c['invitados']} invitados\n"
        f"Paquete: {c['paquete']} · Extras: {extras}\n"
        f"Estimado: Bs {c['estimado_bob']}"
    )


def _correo(c: Dict) -> None:
    host, to = os.getenv("SMTP_HOST"), os.getenv("ADMIN_EMAIL")
    if not (host and to):
        log.info("SMTP_HOST/ADMIN_EMAIL no configurados; correo omitido")
        return
    msg = EmailMessage()
    msg["Subject"] = f"Nueva cotización — {c['nombre']} ({c['tipo_evento']}, {c['fecha']})"
    msg["From"] = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "no-reply@localhost"))
    msg["To"] = to
    msg.set_content(_resumen(c))
    with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=15) as s:
        s.starttls()
        if os.getenv("SMTP_USER"):
            s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD", ""))
        s.send_message(msg)


async def _whatsapp(c: Dict) -> None:
    token, phone_id, to = (os.getenv(k) for k in ("WHATSAPP_TOKEN", "WHATSAPP_PHONE_ID", "WHATSAPP_ADMIN_TO"))
    if not (token and phone_id and to):
        return
    # Fuera de la ventana de 24 h la Cloud API exige una plantilla aprobada (type="template").
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            f"https://graph.facebook.com/v20.0/{phone_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": _resumen(c)}},
        )
        r.raise_for_status()


async def notificar_cotizacion(c: Dict) -> None:
    tareas = {"correo": asyncio.to_thread(_correo, c), "whatsapp": _whatsapp(c)}
    for i, fn in enumerate(_listeners):
        async def _run(fn=fn):
            r = fn(c)
            if inspect.isawaitable(r):
                await r
        tareas[f"listener{i}"] = _run()
    for nombre, res in zip(tareas, await asyncio.gather(*tareas.values(), return_exceptions=True)):
        if isinstance(res, Exception):
            log.error("Notificación %s falló: %s", nombre, res)
