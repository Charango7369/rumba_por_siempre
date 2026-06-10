from fastapi import APIRouter

router = APIRouter()


@router.post("/")
def enviar_contacto():
    return {"message": "Formulario de contacto recibido"}