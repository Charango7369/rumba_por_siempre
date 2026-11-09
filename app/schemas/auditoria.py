from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime

class AuditoriaResponse(BaseModel):
    id: int
    usuario_id: Optional[int] = None
    usuario_email: str
    rol_ejecutor: str
    accion: str
    recurso_afectado: str
    recurso_id: Optional[str] = None
    valores_previos: Optional[Dict[str, Any]] = None
    valores_nuevos: Optional[Dict[str, Any]] = None
    ip: str
    user_agent: Optional[str] = None
    fecha_hora: datetime

    model_config = ConfigDict(from_attributes=True)
