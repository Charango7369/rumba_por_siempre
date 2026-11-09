import logging
from app.database import SessionLocal, engine, Base
from app.models.usuario import Usuario
from app.models.rbac import Rol, Permiso
from app.models.servicio import Servicio
from app.models.configuracion import Configuracion
from app.utils.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

# 1. Definición de Permisos del Sistema
PERMISOS_SISTEMA = [
    # Dashboard
    {"codigo": "dashboard:view", "modulo": "dashboard", "descripcion": "Visualizar métricas del dashboard"},
    # Catálogo
    {"codigo": "catalog:read", "modulo": "catalog", "descripcion": "Visualizar servicios en panel administrativo"},
    {"codigo": "catalog:create", "modulo": "catalog", "descripcion": "Crear nuevos servicios o extras"},
    {"codigo": "catalog:update", "modulo": "catalog", "descripcion": "Editar fichas técnicas y descripciones de servicios"},
    {"codigo": "catalog:pricing", "modulo": "catalog", "descripcion": "Modificar precios base y promociones"},
    {"codigo": "catalog:toggle", "modulo": "catalog", "descripcion": "Activar o desactivar servicios del catálogo público"},
    {"codigo": "catalog:delete", "modulo": "catalog", "descripcion": "Eliminar servicios del catálogo"},
    # Cotizaciones
    {"codigo": "quotes:read", "modulo": "quotes", "descripcion": "Consultar solicitudes y cotizaciones recibidas"},
    {"codigo": "quotes:update_status", "modulo": "quotes", "descripcion": "Actualizar estado operativo de la cotización"},
    {"codigo": "quotes:notes", "modulo": "quotes", "descripcion": "Registrar notas u observaciones comerciales"},
    {"codigo": "quotes:delete", "modulo": "quotes", "descripcion": "Eliminar cotizaciones del sistema"},
    # Usuarios y Auditoría
    {"codigo": "users:manage", "modulo": "users", "descripcion": "Administración de usuarios y asignación de roles"},
    {"codigo": "audit:read", "modulo": "audit", "descripcion": "Acceso a registros de auditoría y trazabilidad"},
]

# 2. Definición de Roles y su asignación de permisos
ROLES_CONFIG = {
    "superadmin": {
        "nombre": "SuperAdministrador",
        "descripcion": "Control total del sistema, usuarios, roles, catálogo y auditoría",
        "es_sistema": True,
        "permisos": ["*"]  # Acceso global
    },
    "admin": {
        "nombre": "Administrador",
        "descripcion": "Gestión operativa del catálogo, precios, promociones e imágenes y cotizaciones",
        "es_sistema": True,
        "permisos": [
            "dashboard:view", "catalog:read", "catalog:create", "catalog:update",
            "catalog:pricing", "catalog:toggle", "quotes:read", "quotes:update_status", "quotes:notes"
        ]
    },
    "comercial": {
        "nombre": "Operador Comercial",
        "descripcion": "Atención y seguimiento de solicitudes de cotización",
        "es_sistema": True,
        "permisos": [
            "dashboard:view", "catalog:read", "quotes:read", "quotes:update_status", "quotes:notes"
        ]
    }
}

# 3. Servicios Principales del Catálogo RXS
SERVICIOS_BASE = [
    {
        "nombre": "Sonido Básico",
        "slug": "sonido-basico",
        "categoria": "Sonido",
        "precio_base": 1800.0,
        "precio_promocional": None,
        "descripcion_corta": "Claridad acústica ideal para reuniones pequeñas, conferencias o eventos de hasta 150 personas.",
        "descripcion_larga": "Sistema acústico profesional calibrado para espacios cerrados o medianos. Incluye 2 cajas acústicas activas de alta fidelidad, consola digital de 12 canales, 2 micrófonos inalámbricos Shure y técnico de sonido.",
        "imagen_principal": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=800&q=80",
        "galeria_imagenes": [
            "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1465847899084-d164df4dedc6?auto=format&fit=crop&w=800&q=80"
        ],
        "especificaciones_tecnicas": ["2x Parlantes Activos Pro", "Consola Digital 12ch", "2x Microfonía Shure Wireless", "Operador de Audio"],
        "es_extra": False,
        "activo": True,
        "destacado": False,
        "orden_visualizacion": 1
    },
    {
        "nombre": "Estructura e Iluminación Profesional",
        "slug": "iluminacion-profesional",
        "categoria": "Iluminación",
        "precio_base": 3200.0,
        "precio_promocional": 2900.0,
        "descripcion_corta": "Show de luces robóticas sincronizadas DMX sobre puente truss de aluminio certificado.",
        "descripcion_larga": "Estructura modular truss de alta resistencia con iluminación computarizada. Diseñado para transformar cualquier salón o escenario abierto con haces de luz de largo alcance, cabezas móviles beam y ambientación wash perimetral.",
        "imagen_principal": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=800&q=80",
        "galeria_imagenes": [
            "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1506157786151-b8491531f063?auto=format&fit=crop&w=800&q=80"
        ],
        "especificaciones_tecnicas": ["8x Cabezas Móviles Beam 7R", "Puente Truss 6 Metros", "Controlador DMX por Software", "Bañadores LED RGBW"],
        "es_extra": False,
        "activo": True,
        "destacado": True,
        "orden_visualizacion": 2
    },
    {
        "nombre": "Paquete Completo Rumba Apolo",
        "slug": "paquete-rumba-apolo",
        "categoria": "Paquetes",
        "precio_base": 5200.0,
        "precio_promocional": 4800.0,
        "descripcion_corta": "Producción técnica integral con sonido Line Array Nexo STM, iluminación robótica y DJ profesional.",
        "descripcion_larga": "La máxima experiencia de ingeniería técnica para bodas de gala, aniversarios masivos y festivales. Incluye torres de sonido Line Array con presión acústica homogénea, iluminación de alto impacto, cabina Pioneer DJ y operadores dedicados durante todo el evento.",
        "imagen_principal": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=800&q=80",
        "galeria_imagenes": [
            "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1519671482749-fd09be7ccebf?auto=format&fit=crop&w=800&q=80"
        ],
        "especificaciones_tecnicas": ["Sonido Line Array Nexo STM", "Subwoofers Dobles de Alta Pegada", "Iluminación Robótica + Láser", "Cabina Pioneer DJ Nexus 2", "Transporte & Montaje Completo"],
        "es_extra": False,
        "activo": True,
        "destacado": True,
        "orden_visualizacion": 3
    },
    # Extras dinámicos para cotizador
    {
        "nombre": "Pantallas LED",
        "slug": "pantallas",
        "categoria": "Video",
        "precio_base": 900.0,
        "precio_promocional": None,
        "descripcion_corta": "Módulo de pantalla LED P3.9 de alta definición para visuales y circuitos cerrados.",
        "descripcion_larga": "Pantalla LED para proyección de videos, transmisión en vivo o fondos escenográficos.",
        "imagen_principal": "https://images.unsplash.com/photo-1506157786151-b8491531f063?auto=format&fit=crop&w=800&q=80",
        "galeria_imagenes": [],
        "especificaciones_tecnicas": ["Pitch 3.9mm High Refresh", "Procesador de Video HDMI"],
        "es_extra": True,
        "activo": True,
        "destacado": False,
        "orden_visualizacion": 10
    },
    {
        "nombre": "Máquina de Humo",
        "slug": "humo",
        "categoria": "Efectos",
        "precio_base": 350.0,
        "precio_promocional": None,
        "descripcion_corta": "Efecto atmosférico Hazer para realzar haces de luz robótica.",
        "descripcion_larga": "Máquina de humo denso con control inalámbrico y líquido no tóxico a base de agua.",
        "imagen_principal": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=800&q=80",
        "galeria_imagenes": [],
        "especificaciones_tecnicas": ["Control DMX y Remoto", "Líquido Neutro Inodoro"],
        "es_extra": True,
        "activo": True,
        "destacado": False,
        "orden_visualizacion": 11
    },
    {
        "nombre": "Animación / DJ",
        "slug": "animacion",
        "categoria": "Personal",
        "precio_base": 600.0,
        "precio_promocional": None,
        "descripcion_corta": "DJ profesional con repertorio musical crossover y animación de pista.",
        "descripcion_larga": "DJ residente con equipamiento Pioneer y animación para mantener la fiesta encendida.",
        "imagen_principal": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=800&q=80",
        "galeria_imagenes": [],
        "especificaciones_tecnicas": ["Showman Animador", "Música Actualizada"],
        "es_extra": True,
        "activo": True,
        "destacado": False,
        "orden_visualizacion": 12
    },
    {
        "nombre": "Streaming en vivo",
        "slug": "streaming",
        "categoria": "Video",
        "precio_base": 800.0,
        "precio_promocional": None,
        "descripcion_corta": "Transmisión multicámara Full HD a YouTube / Facebook con enlace dedicado.",
        "descripcion_larga": "Producción audiovisual en vivo para familiares o público que no puede asistir físicamente.",
        "imagen_principal": "https://images.unsplash.com/photo-1465847899084-d164df4dedc6?auto=format&fit=crop&w=800&q=80",
        "galeria_imagenes": [],
        "especificaciones_tecnicas": ["2x Cámaras Sony Pro", "Switch Blackmagic ATEM"],
        "es_extra": True,
        "activo": True,
        "destacado": False,
        "orden_visualizacion": 13
    }
]

def seed_data():
    logger.info("Iniciando sembrado de base de datos (Seed RBAC + Catálogo RXS)...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Crear Permisos
        permisos_map = {}
        for p_data in PERMISOS_SISTEMA:
            perm = db.query(Permiso).filter(Permiso.codigo == p_data["codigo"]).first()
            if not perm:
                perm = Permiso(**p_data)
                db.add(perm)
                db.commit()
                db.refresh(perm)
                logger.info(f"Permiso creado: {perm.codigo}")
            permisos_map[perm.codigo] = perm

        # 2. Crear Roles y asignar permisos
        roles_map = {}
        for r_code, r_info in ROLES_CONFIG.items():
            rol = db.query(Rol).filter(Rol.codigo == r_code).first()
            if not rol:
                rol = Rol(
                    codigo=r_code,
                    nombre=r_info["nombre"],
                    descripcion=r_info["descripcion"],
                    es_sistema=r_info["es_sistema"]
                )
                db.add(rol)
                db.commit()
                db.refresh(rol)
                logger.info(f"Rol creado: {rol.codigo}")

            # Asignar permisos al rol
            if r_info["permisos"] == ["*"]:
                rol.permisos = list(permisos_map.values())
            else:
                rol.permisos = [permisos_map[c] for c in r_info["permisos"] if c in permisos_map]
            db.commit()
            roles_map[r_code] = rol

        # 3. Crear Usuario SuperAdministrador con Argon2id
        admin_email = "admin@rumbaporsiempre.com"
        admin = db.query(Usuario).filter(Usuario.email == admin_email).first()
        if not admin:
            admin = Usuario(
                nombre="Dr. Edwin Rivero",
                email=admin_email,
                hashed_password=get_password_hash("RumbaAdmin2026!"),
                rol="superadmin",
                activo=True
            )
            admin.roles = [roles_map["superadmin"]]
            db.add(admin)
            db.commit()
            logger.info("Usuario SuperAdministrador creado: admin@rumbaporsiempre.com")
        else:
            admin.hashed_password = get_password_hash("RumbaAdmin2026!")
            admin.roles = [roles_map["superadmin"]]
            db.commit()

        # Crear Usuario Operador Comercial de prueba
        comercial_email = "ventas@rumbaporsiempre.com"
        comercial = db.query(Usuario).filter(Usuario.email == comercial_email).first()
        if not comercial:
            comercial = Usuario(
                nombre="Operador Comercial RXS",
                email=comercial_email,
                hashed_password=get_password_hash("VentasRxS2026!"),
                rol="comercial",
                activo=True
            )
            comercial.roles = [roles_map["comercial"]]
            db.add(comercial)
            db.commit()
            logger.info("Usuario Operador Comercial creado: ventas@rumbaporsiempre.com")

        # 4. Sembrar Catálogo de Servicios
        for s_data in SERVICIOS_BASE:
            servicio = db.query(Servicio).filter(Servicio.slug == s_data["slug"]).first()
            if not servicio:
                nuevo_s = Servicio(**s_data)
                db.add(nuevo_s)
                logger.info(f"Servicio agregado al catálogo: {s_data['nombre']}")
            else:
                # Actualizar precios y descripciones
                for k, v in s_data.items():
                    setattr(servicio, k, v)
                logger.info(f"Servicio actualizado: {s_data['nombre']}")
        db.commit()

        # 5. Sembrar Configuraciones del Cotizador
        configs = [
            {"clave": "CAPACIDAD_BASE_INVITADOS", "valor": "150", "tipo_dato": "int", "descripcion": "Invitados incluidos en precio base"},
            {"clave": "TAMANO_BLOQUE_INVITADOS", "valor": "50", "tipo_dato": "int", "descripcion": "Bloque de invitados adicionales"},
            {"clave": "COSTO_POR_BLOQUE_INVITADOS", "valor": "180.0", "tipo_dato": "float", "descripcion": "Costo por bloque adicional en Bs."}
        ]
        for c in configs:
            conf_obj = db.query(Configuracion).filter(Configuracion.clave == c["clave"]).first()
            if not conf_obj:
                db.add(Configuracion(**c))
        db.commit()

        logger.info("¡Seeding completado exitosamente! Base de datos inicializada con RBAC y catálogo dinámico.")

    except Exception as e:
        db.rollback()
        logger.exception(f"Error durante el seed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
