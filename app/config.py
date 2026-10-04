import os
from dotenv import load_dotenv

load_dotenv()

# ── Base de datos (sin cambios) ───────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Falta la variable de entorno DATABASE_URL")

# Algunos proveedores entregan "postgres://"; SQLAlchemy 2.x exige "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


# ── Entorno ───────────────────────────────────────────────────────────────────
# En Railway define ENV=production. Sin esa variable se asume desarrollo.
IS_PRODUCTION = os.getenv("ENV", "development").lower() == "production"


# ── CORS ──────────────────────────────────────────────────────────────────────
def _lista(valor: str) -> list[str]:
    """Convierte "a, b/ ,c" en ["a", "b", "c"]: sin espacios ni barra final."""
    return [v.strip().rstrip("/") for v in valor.split(",") if v.strip()]


# Orígenes explícitos (dominio de Pages y dominio propio). Misma variable de siempre.
# En desarrollo, si no está definida, se usan los puertos habituales de Vite.
_default_cors = "" if IS_PRODUCTION else "http://localhost:5173,http://127.0.0.1:5173"
CORS_ORIGINS = _lista(os.getenv("CORS_ORIGINS", _default_cors))

# localhost/127.0.0.1 en cualquier puerto: cubre `npm run dev` (5173)
# y `npm run preview` (4173). Solo se activa fuera de producción.
_LOCAL_REGEX = r"http://(localhost|127\.0\.0\.1)(:\d+)?"

# Regex opcional para los previews de Cloudflare Pages, por ejemplo:
# CORS_ORIGIN_REGEX=https://([a-z0-9-]+\.)?TU-PROYECTO\.pages\.dev
_extra_regex = os.getenv("CORS_ORIGIN_REGEX", "").strip()

if IS_PRODUCTION:
    CORS_ORIGIN_REGEX = _extra_regex or None
else:
    CORS_ORIGIN_REGEX = f"({_LOCAL_REGEX})" + (f"|({_extra_regex})" if _extra_regex else "")

# Aviso temprano: en producción sin orígenes, el navegador bloqueará todo el frontend.
if IS_PRODUCTION and not CORS_ORIGINS and not CORS_ORIGIN_REGEX:
    print("ADVERTENCIA: ENV=production pero CORS_ORIGINS está vacío; el frontend será bloqueado por CORS.")


# ── WhatsApp ──────────────────────────────────────────────────────────────────
# Formato internacional, sin "+". Se puede sobrescribir desde Railway.
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "59172836437")