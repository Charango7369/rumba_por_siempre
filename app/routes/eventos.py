from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def listar_eventos():
    return {"eventos": []}