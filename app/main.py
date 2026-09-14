from datetime import date

from fastapi import FastAPI, Request
from app.database import engine, Base
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from app.api.routes import router as leads_router # Importamos las rutas
from app.models.lead import Lead
from app.models.evento import Evento
from app.models.servicio import Servicio
from app.models.usuario import Usuario

# 2. Crea las tablas en la base de datos
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Rumba X Siempre API", version="1.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tu-dominio-en-cloudflare.pages.dev", "http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=86400,
)

# Acoplamos el enrutador a la aplicación principal
app.include_router(leads_router, prefix="/api")

@app.get("/")
async def root():
    return {"status": "API operativa", "motor": "Postgres asíncrono"}

class CotizacionRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    telefono: str = Field(min_length=6, max_length=24)
    ciudad: str = Field(min_length=2, max_length=80)
    fecha: date
    tipo_evento: str = Field(min_length=2, max_length=60)
    invitados: int = Field(ge=20, le=5000)
    paquete: str = Field(min_length=2, max_length=40)
    extras: list[str] = []


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


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


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


def build_whatsapp_message(resumen: dict) -> str:
    extras = ", ".join(resumen["extras"]) if resumen["extras"] else "sin extras"
    text = (
        "Hola RxS, quiero reservar sonido y luces.%0A"
        f"Nombre: {resumen['nombre']}%0A"
        f"Telefono: {resumen['telefono']}%0A"
        f"Ciudad: {resumen['ciudad']}%0A"
        f"Fecha: {resumen['fecha']}%0A"
        f"Evento: {resumen['tipo_evento']}%0A"
        f"Invitados: {resumen['invitados']}%0A"
        f"Paquete: {resumen['paquete']}%0A"
        f"Extras: {extras}%0A"
        f"Estimado: Bs {resumen['estimado_bob']}"
    )
    return f"https://wa.me/59172836437?text={text}"