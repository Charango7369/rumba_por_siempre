from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadResponse
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
    
    # Purgar solicitudes que ya salieron de la ventana de tiempo
    IP_RATES[ip] = [t for t in IP_RATES[ip] if current_time - t < TIME_WINDOW]
    
    if len(IP_RATES[ip]) >= MAX_REQUESTS:
        raise HTTPException(
            status_code=429, 
            detail="Se ha superado el límite de cotizaciones por hora. Por favor, contáctanos directamente por teléfono."
        )
    
    IP_RATES[ip].append(current_time)

# --- ENDPOINT PRINCIPAL ---
@router.post("/leads", response_model=LeadResponse, dependencies=[Depends(rate_limiter)])
async def create_lead(lead: LeadCreate, db: AsyncSession = Depends(get_db)):
    db_lead = Lead(
        nombre=lead.nombre,
        telefono=lead.telefono,
        tipo_evento=lead.tipo_evento,
        fecha_estimada=lead.fecha,
        estado="Pendiente"
    )
    
    db.add(db_lead)
    
    try:
        await db.commit()
        await db.refresh(db_lead)
        return db_lead
    except IntegrityError:
        # El motor Postgres bloqueó el registro por el UniqueConstraint
        await db.rollback()
        raise HTTPException(
            status_code=400, 
            detail="Ya hemos registrado una cotización para este número telefónico en esta misma fecha."
        )