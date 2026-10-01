import logging

from app.database import SessionLocal, engine, Base
from app.models.usuario import Usuario  # noqa: F401 (se importan para registrar todos los modelos)
from app.models.lead import Lead  # noqa: F401
from app.models.evento import Evento  # noqa: F401
from app.models.servicio import Servicio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVICIOS_BASE = [
    {
        "nombre": "Sonido Básico",
        "categoria": "Sonido",
        "precio_base": 500.0,
        "descripcion": "Ideal para reuniones pequeñas o conferencias",
    },
    {
        "nombre": "Estructura e Iluminación Profesional",
        "categoria": "Iluminación",
        "precio_base": 1200.0,
        "descripcion": "Cabezas móviles, luces LED perimetrales y puente de luces",
    },
    {
        "nombre": "Paquete Completo Rumba Apolo",
        "categoria": "Paquetes",
        "precio_base": 2500.0,
        "descripcion": "Sonido line array, iluminación completa y DJ",
    },
]


def seed_servicios():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for serv in SERVICIOS_BASE:
            existe = db.query(Servicio).filter(Servicio.nombre == serv["nombre"]).first()
            if not existe:
                db.add(Servicio(**serv))
                logger.info("Servicio agregado: %s", serv["nombre"])
        db.commit()
        logger.info("Seed de servicios completado.")
    except Exception:
        db.rollback()
        logger.exception("Error durante el seed")
    finally:
        db.close()


if __name__ == "__main__":
    seed_servicios()