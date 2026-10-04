from datetime import date
from urllib.parse import quote

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# Importaciones de la base de datos y enrutadores
from app.database import engine, Base
from app.config import CORS_ORIGINS, CORS_ORIGIN_REGEX, WHATSAPP_NUMBER
from app.api.routes import router as api_router  # incluye leads y servicios
from app.models.lead import Lead
from app.models.evento import Evento
from app.models.servicio import Servicio
from app.models.usuario import Usuario

# 1. Crea las tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rumba X Siempre API", version="1.0.0")

# 2. Archivos estáticos y plantillas.
# check_dir=False: git no sube carpetas vacías; sin esto, si "static/" no existe
# en Railway la app se cae al arrancar con RuntimeError.
app.mount("/static", StaticFiles(directory="static", check_dir=False), name="static")
templates = Jinja2Templates(directory="templates")

# 3. CORS para el frontend React.
# - allow_origins: dominios explícitos (Pages, dominio propio) desde ALLOWED_ORIGINS.
# - allow_origin_regex: localhost en cualquier puerto (solo en desarrollo) y previews de Pages.
# Un origen se acepta si coincide con cualquiera de los dos.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=False,  # sin cookies de sesión; True solo si la auth usa cookies
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    max_age=86400,
)

# 4. Enrutador principal con el prefijo /api
app.include_router(api_router, prefix="/api")


# 5. Rutas directas

@app.get("/")
async def root():
    return {"status": "API operativa"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/home", response_class=HTMLResponse)
def home(request: Request):
    # Movido a /home para no hacer conflicto con la raíz
    return templates.TemplateResponse(request, "index.html")


# 6. Lógica de cotización automática y WhatsApp

class CotizacionRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    telefono: str = Field(min_length=6, max_length=24)
    ciudad: str = Field(min_length=2, max_length=80)
    fecha: date
    tipo_evento: str = Field(min_length=2, max_length=60)
    invitados: int = Field(ge=20, le=5000)
    paquete: str = Field(min_length=2, max_length=40)
    extras: list[str] = Field(default_factory=list, max_length=10)


BASE_PRICES = {
    "esencial": 1800,
    "premium": 3200,
    "pro": 5200,
}

EXTRA_PRICES = {
    "pantallas": 900,
    "humo": 350,
    "animacion": 600,
    "streaming": 800,
}


def build_whatsapp_message(resumen: dict) -> str:
    extras = ", ".join(resumen["extras"]) if resumen["extras"] else "sin extras"
    lineas = [
        "Hola RxS, quiero reservar sonido y luces.",
        f"Nombre: {resumen['nombre']}",
        f"Telefono: {resumen['telefono']}",
        f"Ciudad: {resumen['ciudad']}",
        f"Fecha: {resumen['fecha']}",
        f"Evento: {resumen['tipo_evento']}",
        f"Invitados: {resumen['invitados']}",
        f"Paquete: {resumen['paquete']}",
        f"Extras: {extras}",
        f"Estimado: Bs {resumen['estimado_bob']}",
    ]
    # quote() codifica espacios, tildes, "&", "#", etc. y convierte "\n" en %0A.
    # Sin esto, un nombre como "Pérez & Hijos" o una ciudad con "#" rompe el enlace.
    texto = quote("\n".join(lineas), safe="")
    return f"https://wa.me/{WHATSAPP_NUMBER}?text={texto}"


@app.post("/api/cotizacion")
def crear_cotizacion(payload: CotizacionRequest):
    paquete = payload.paquete.lower()
    base = BASE_PRICES.get(paquete, BASE_PRICES["premium"])
    capacidad = max(0, payload.invitados - 150) // 50 * 180
    extras = sum(EXTRA_PRICES.get(extra, 0) for extra in payload.extras)
    total = base + capacidad + extras

    resumen = {
        "nombre": payload.nombre,
        "telefono": payload.telefono,
        "ciudad": payload.ciudad,
        "fecha": payload.fecha.isoformat(),
        "tipo_evento": payload.tipo_evento,
        "invitados": payload.invitados,
        "paquete": paquete,
        "extras": payload.extras,
        "estimado_bob": total,
    }

    return {
        "message": "Cotizacion estimada generada",
        "resumen": resumen,
        "whatsapp": build_whatsapp_message(resumen),
    }