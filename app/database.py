from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Cambia esta URL si usas PostgreSQL: "postgresql://usuario:password@localhost:5432/tu_base_de_datos"
SQLALCHEMY_DATABASE_URL = "sqlite:///./rumba_por_siempre.db"

# engine = create_engine(SQLALCHEMY_DATABASE_URL) # Usa este si es PostgreSQL
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} # check_same_thread es solo para SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Esta es la función que FastAPI estaba buscando
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()