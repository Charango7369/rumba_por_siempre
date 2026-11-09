import logging
from urllib.parse import quote

from fastapi import BackgroundTasks, Depends, FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# Importaciones de BD, configuración y modelos
from app.database import engine, Base, get_db
from app.config import CORS_ORIGINS, CORS_ORIGIN_REGEX, WHATSAPP_NUMBER
import app.models  # Registra todos los modelos

# Routers v1 Enterprise
from app.api.v1.auth import router as auth_router
from app.api.v1.servicios_publicos import router as servicios_v1_router
from app.api.v1.admin_servicios import router as admin_servicios_router
from app.api.v1.admin_cotizaciones import router as admin_cotizaciones_v1_router
from app.api.v1.admin_usuarios import router as admin_usuarios_router
from app.api.v1.admin_auditoria import router as admin_auditoria_router
from app.api.v1.admin_metricas import router as admin_metricas_router

# Routers Legacy / Compatibilidad
from app.api.routes import router as legacy_api_router
from app.models.cotizacion import Cotizacion
from app.schemas.cotizacion import CotizacionRequest
from app.services.cotizaciones import calcular_cotizacion_dinamica, generar_codigo_seguimiento
from app.services.errores_es import traducir_errores
from app.services.notificaciones import notificar_cotizacion
from app.services.ratelimit import rate_limit

# Crear tablas si no existen (idempotente)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Rumba X Siempre API - Enterprise",
    version="2.0.0",
    description="Plataforma SaaS para producción técnica de eventos y gestión de catálogo."
)

# Manejador de errores de validación amigables en español
@app.exception_handler(RequestValidationError)
async def errores_de_validacion(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": jsonable_encoder(exc.errors()),
            "errores": traducir_errores(exc.errors()),
        },
    )

# Archivos estáticos y plantillas
app.mount("/static", StaticFiles(directory="static", check_dir=False), name="static")
templates = Jinja2Templates(directory="templates")

# Configuración CORS permisiva para desarrollo y estricta en producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,
)

# Registro de Routers Enterprise v1
app.include_router(auth_router, prefix="/api/v1")
app.include_router(servicios_v1_router, prefix="/api/v1")
app.include_router(admin_servicios_router, prefix="/api/v1")
app.include_router(admin_cotizaciones_v1_router, prefix="/api/v1")
app.include_router(admin_usuarios_router, prefix="/api/v1")
app.include_router(admin_auditoria_router, prefix="/api/v1")
app.include_router(admin_metricas_router, prefix="/api/v1")

# Routers Legacy para clientes existentes
app.include_router(legacy_api_router, prefix="/api")

log = logging.getLogger("cotizaciones")

@app.get("/")
async def root():
    return {
        "status": "API operativa",
        "version": "2.0.0",
        "sistema": "Rumba X Siempre Enterprise SaaS"
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/home", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")

def build_whatsapp_message(resumen: dict) -> str:
    extras_txt = ", ".join(resumen.get("extras", [])) if resumen.get("extras") else "sin extras"
    lineas = [
        "Hola RxS, quiero reservar sonido y luces.",
        f"Código: {resumen.get('codigo_seguimiento', 'S/N')}",
        f"Nombre: {resumen['nombre']}",
        f"Teléfono: {resumen['telefono']}",
        f"Ciudad: {resumen['ciudad']}",
        f"Fecha: {resumen['fecha']}",
        f"Evento: {resumen['tipo_evento']}",
        f"Invitados: {resumen['invitados']}",
        f"Paquete: {resumen['paquete']}",
        f"Extras: {extras_txt}",
        f"Estimado: Bs. {resumen['estimado_bob']}",
    ]
    texto = quote("\n".join(lineas), safe="")
    return f"https://wa.me/{WHATSAPP_NUMBER}?text={texto}"

@app.post("/api/cotizacion", dependencies=[Depends(rate_limit)])
@app.post("/api/v1/quotes", dependencies=[Depends(rate_limit)])
def crear_cotizacion(
    payload: CotizacionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # Cálculo 100% dinámico respaldado por base de datos
    total, desglose, servicio_obj = calcular_cotizacion_dinamica(payload, db)
    codigo_seg = generar_codigo_seguimiento(db)

    resumen = {
        "codigo_seguimiento": codigo_seg,
        "nombre": payload.nombre,
        "telefono": payload.telefono,
        "ciudad": payload.ciudad,
        "fecha": payload.fecha_evento.isoformat(),
        "tipo_evento": payload.tipo_evento,
        "invitados": payload.invitados,
        "paquete": payload.paquete,
        "extras": payload.extras,
        "estimado_bob": total,
        "desglose": desglose
    }

    cotizacion_id = None
    try:
        registro = Cotizacion(
            codigo_seguimiento=codigo_seg,
            nombre=payload.nombre,
            telefono=payload.telefono,
            ciudad=payload.ciudad,
            fecha_evento=payload.fecha_evento,
            tipo_evento=payload.tipo_evento,
            invitados=payload.invitados,
            paquete=payload.paquete,
            extras=payload.extras,
            servicio_id=servicio_obj.id if servicio_obj else None,
            total_estimado=total,
            desglose_calculo=desglose,
            estado="Pendiente"
        )
        db.add(registro)
        db.commit()
        db.refresh(registro)
        cotizacion_id = registro.id
    except SQLAlchemyError:
        db.rollback()
        log.exception("Error al persistir la cotización en BD")

    background_tasks.add_task(notificar_cotizacion, {**resumen, "id": cotizacion_id})

    return {
        "message": "Cotización estimada generada con catálogo en vivo",
        "id": cotizacion_id,
        "codigo_seguimiento": codigo_seg,
        "resumen": resumen,
        "whatsapp": build_whatsapp_message(resumen),
    }
