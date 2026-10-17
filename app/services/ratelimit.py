import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

_VENTANA, _MAX = 60, 10
_hits: dict = defaultdict(deque)


def rate_limit(request: Request) -> None:
    """Límite por IP en memoria (por proceso). Detrás del proxy de Railway usa X-Forwarded-For;
    ese header puede falsificarse, así que es freno anti-abuso básico, no una barrera de seguridad."""
    fwd = request.headers.get("x-forwarded-for", "")
    ip = fwd.split(",")[0].strip() or (request.client.host if request.client else "?")
    q, ahora = _hits[ip], time.monotonic()
    while q and ahora - q[0] > _VENTANA:
        q.popleft()
    if len(q) >= _MAX:
        raise HTTPException(status_code=429, detail="Demasiados intentos. Espera un minuto.")
    q.append(ahora)
