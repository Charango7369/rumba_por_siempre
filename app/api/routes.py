from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session  # <-- Usamos Session síncrona
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.database import get_db
from app.models.lead import Lead
from app.models.servicio import Servicio
from app.schemas.lead import LeadCreate, LeadResponse
from app.schemas.servicio import ServicioResponse
import time

router = APIRouter()

# --- RATE LIMITER EN MEMORIA ---
IP_RATES = {}
MAX_REQUESTS = 3
TIME_WINDOW = 3600  # 3600 segundos = 1 hora

async def rate_limiter(request: Request):
    ip = request.client.host
    current_time = time.time()
    
    if ip not in IP_RATES:
        IP_RATES[ip] = []
    
    IP_RATES[ip] = [t for t in IP_RATES[ip] if current_time - t < TIME_WINDOW]
    
    if len(IP_RATES[ip]) >= MAX_REQUESTS:
        raise HTTPException(
            status_code=429, 
            detail="Se ha superado el límite de cotizaciones por hora. Por favor, contáctanos directamente por teléfono."
        )
    
    IP_RATES[ip].append(current_time)

# --- ENDPOINTS ---

@router.post("/leads", response_model=LeadResponse, dependencies=[Depends(rate_limiter)])
def create_lead(lead: LeadCreate, db: Session = Depends(get_db)): # <-- def normal (sin async)
    db_lead = Lead(
        nombre=lead.nombre,
        telefono=lead.telefono,
        tipo_evento=lead.tipo_evento,
        fecha_estimada=lead.fecha,
        estado="Pendiente"
    )
    
    db.add(db_lead)
    
    try:
        db.commit() # <-- Sin await
        db.refresh(db_lead) # <-- Sin await
        return db_lead
    except IntegrityError:
        db.rollback() # <-- Sin await
        raise HTTPException(
            status_code=400, 
            detail="Ya hemos registrado una cotización para este número telefónico en esta misma fecha."
        )

@router.get("/servicios", response_model=list[ServicioResponse], summary="Listar todos los servicios de Rumba por Siempre")
def obtener_servicios(db: Session = Depends(get_db)): # <-- def normal (sin async)
    """
    Consulta la base de datos de forma síncrona y devuelve los servicios.
    """
    result = db.execute(select(Servicio)) # <-- Sin await
    servicios = result.scalars().all()
    return servicios