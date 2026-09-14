from pydantic import BaseModel, Field
from datetime import date

class LeadCreate(BaseModel):
    nombre: str = Field(..., max_length=100, description="Nombre completo del cliente")
    # Validación estricta del formato telefónico boliviano
    telefono: str = Field(..., pattern=r"^[67]\d{7}$", description="WhatsApp de 8 dígitos")
    tipo_evento: str = Field(..., max_length=50)
    fecha: date

class LeadResponse(BaseModel):
    id: int
    nombre: str
    estado: str

    class Config:
        from_attributes = True