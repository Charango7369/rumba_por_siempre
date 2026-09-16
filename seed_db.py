import logging
from app.database import SessionLocal, engine, Base
from app.models.usuario import Usuario
from app.models.servicio import Servicio
from app.models.lead import Lead

# Configuramos el logger para ver qué sucede en la consola
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_data():
    logger.info("Iniciando la población de la base de datos (Seeding)...")
    db = SessionLocal()

    try:
        # 1. Crear Usuario Administrador principal
        admin_email = "admin@rumbaporsiempre.com"
        admin = db.query(Usuario).filter(Usuario.email == admin_email).first()
        if not admin:
            # Nota: Asegúrate de hashear la contraseña en producción usando app.utils.security
            nuevo_admin = Usuario(
                nombre="Dr. Edwin Rivero", 
                email=admin_email,
                hashed_password="hash_temporal_123", # Cambiar por get_password_hash("tu_password")
                rol="admin",
                activo=True
            )
            db.add(nuevo_admin)
            logger.info("Usuario administrador creado: Dr. Edwin Rivero")

        # 2. Crear Servicios de Producción Técnica
        servicios_base = [
            {
                "nombre": "Sonido Básico", 
                "categoria": "Sonido", 
                "precio_base": 500.0, 
                "descripcion": "Ideal para reuniones pequeñas o conferencias"
            },
            {
                "nombre": "Estructura e Iluminación Profesional", 
                "categoria": "Iluminación", 
                "precio_base": 1200.0, 
                "descripcion": "Cabezas móviles, luces LED perimetrales y puente de luces"
            },
            {
                "nombre": "Paquete Completo Rumba Apolo", 
                "categoria": "Paquetes", 
                "precio_base": 2500.0, 
                "descripcion": "Sonido line array, iluminación completa y DJ"
            }
        ]
        
        for serv in servicios_base:
            existe = db.query(Servicio).filter(Servicio.nombre == serv["nombre"]).first()
            if not existe:
                nuevo_servicio = Servicio(**serv)
                db.add(nuevo_servicio)
                logger.info(f"Servicio agregado: {serv['nombre']}")

        # 3. Guardar los cambios en la base de datos
        db.commit()
        logger.info("Seeding completado con éxito. Base de datos lista.")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error durante el seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Opcional: Si necesitas borrar todo y empezar de cero, descomenta las siguientes 2 líneas
    # Base.metadata.drop_all(bind=engine)
    # Base.metadata.create_all(bind=engine)
    
    seed_data()