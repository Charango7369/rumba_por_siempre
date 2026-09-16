from datetime import date
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# Importaciones de la base de datos y enrutadores
from app.database import engine, Base
from app.api.routes import router as api_router  # Renombrado genérico, ya que incluye leads y servicios
from app.models.lead import Lead
from app.models.evento import Evento
from app.models.servicio import Servicio
from app.models.usuario import Usuario

# 1. Crea las tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rumba X Siempre API", version="1.0.0")

# 2. Configuración de archivos estáticos y plantillas (si aún las conservas)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 3. Configuración de CORS para tu frontend en React
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tu-dominio-en-cloudflare.pages.dev", 
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ], 
    allow_credentials=True,
    allow_methods=["*"],  # Modificado para evitar problemas con peticiones OPTIONS de React
    allow_headers=["*"],  # Modificado para aceptar headers asíncronos y de Pydantic
    max_age=86400,
)

# 4. Acoplamos el enrutador principal con el prefijo /api
app.include_router(api_router, prefix="/api")


# 5. Rutas directas

@app.get("/")
async def root():
    # Health Check para Railway
    return {"status": "API operativa", "motor": "Postgres asíncrono"}

@app.get("/home", response_class=HTMLResponse)
def home(request: Request):
    # Movido a /home para no hacer conflicto con la raíz
    return templates.TemplateResponse(request, "index.html")


# 6. Lógica de Cotización Automática y WhatsApp

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