from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routes import eventos, alquileres, contacto

app = FastAPI(title="Rumba Por Siempre")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(eventos.router, prefix="/eventos", tags=["Eventos"])
app.include_router(alquileres.router, prefix="/alquileres", tags=["Alquileres"])
app.include_router(contacto.router, prefix="/contacto", tags=["Contacto"])


@app.get("/")
def home():
    return {"message": "Bienvenido a Rumba Por Siempre"}