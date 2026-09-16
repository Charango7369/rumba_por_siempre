from sqlalchemy.orm import Session
from app.models.lead import Lead
from app.schemas.lead import LeadCreate # Asumiendo que tienes este esquema Pydantic

def get_leads(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Lead).offset(skip).limit(limit).all()

def create_lead(db: Session, lead: LeadCreate):
    db_lead = Lead(
        nombre=lead.nombre,
        telefono=lead.telefono,
        tipo_evento=lead.tipo_evento,
        fecha_estimada=lead.fecha_estimada
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead