import logging
from datetime import date
from urllib.parse import quote

from fastapi import BackgroundTasks, Depends, FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# Importaciones de la base de datos y enrutadores
from app.database import engine, Base, get_db
from app.config import CORS_ORIGINS, CORS_ORIGIN_REGEX, WHATSAPP_NUMBER
from app.api.routes import router as api_router  # incluye leads y servicios
from app.api.admin_cotizaciones import router as admin_cotizaciones_router
from app.models.lead import Lead
from app.models.evento import Evento
from app.models.servicio import Servicio
from app.models.usuario import Usuario
from app.models.cotizacion import Cotizacion  # debe importarse antes de create_all
from app.schemas.cotizacion import BASE_PRICES, EXTRA_PRICES, CotizacionRequest
from app.services.errores_es import traducir_errores
from app.services.notificaciones import notificar_cotizacion
from app.services.ratelimit import rate_limit

# 1. Crea las tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rumba X Siempre API", version="1.0.0")

# Manejador de errores de validación → devuelve mensajes en español
@app.exception_handler(RequestValidationError)
async def errores_de_validacion(request: Request, exc: RequestValidationError):
    """Mismo `detail` de siempre + `errores` {campo: mensaje en español} para mostrar en el formulario."""
    return JSONResponse(
        status_code=422,
        content={
            "detail": jsonable_encoder(exc.errors()),
            "errores": traducir_errores(exc.errors()),
        },
    )

# 2. Archivos estáticos y plantillas
app.mount("/static", StaticFiles(directory="static", check_dir=False), name="static")
templates = Jinja2Templates(directory="templates")

# 3. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    max_age=86400,
)

# 4. Routers
app.include_router(api_router, prefix="/api")
app.include_router(admin_cotizaciones_router, prefix="/api")

# Logger
log = logging.getLogger("cotizaciones")

# 5. Rutas directas
@app.get("/")
async def root():
    return {"status": "API operativa"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/home", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")

# 6. Lógica de cotización automática y WhatsApp
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
    texto = quote("\n".join(lineas), safe="")
    return f"https://wa.me/{WHATSAPP_NUMBER}?text={texto}"

@app.post("/api/cotizacion", dependencies=[Depends(rate_limit)])
def crear_cotizacion(
    payload: CotizacionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    paquete = payload.paquete  # ya normalizado por el schema
    base = BASE_PRICES.get(paquete, BASE_PRICES["premium"])
    capacidad = max(0, payload.invitados - 150) // 50 * 180
    extras = sum(EXTRA_PRICES.get(extra, 0) for extra in payload.extras)
    total = base + capacidad + extras

    resumen = {
        "nombre": payload.nombre,
        "telefono": payload.telefono,
        "ciudad": payload.ciudad,
        "fecha": payload.fecha_evento.isoformat(),
        "tipo_evento": payload.tipo_evento,
        "invitados": payload.invitados,
        "paquete": paquete,
        "extras": payload.extras,
        "estimado_bob": total,
    }

    cotizacion_id = None
    try:
        registro = Cotizacion(
            nombre=payload.nombre,
            telefono=payload.telefono,
            ciudad=payload.ciudad,
            fecha_evento=payload.fecha_evento,
            tipo_evento=payload.tipo_evento,
            invitados=payload.invitados,
            paquete=paquete,
            extras=payload.extras,
        )
        db.add(registro)
        db.commit()
        db.refresh(registro)
        cotizacion_id = registro.id
    except SQLAlchemyError:
        db.rollback()
        log.exception("No se pudo guardar la cotización")

    background_tasks.add_task(notificar_cotizacion, {**resumen, "id": cotizacion_id})

    return {
        "message": "Cotizacion estimada generada",
        "id": cotizacion_id,
        "resumen": resumen,
        "whatsapp": build_whatsapp_message(resumen),
    }
