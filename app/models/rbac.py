from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base

roles_permisos = Table(
    "roles_permisos",
    Base.metadata,
    Column("rol_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permiso_id", Integer, ForeignKey("permisos.id", ondelete="CASCADE"), primary_key=True),
)

usuarios_roles = Table(
    "usuarios_roles",
    Base.metadata,
    Column("usuario_id", Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True),
    Column("rol_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

class Permiso(Base):
    __tablename__ = "permisos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(80), unique=True, nullable=False, index=True)  # Ej: "catalog:pricing"
    modulo = Column(String(50), nullable=False, index=True)  # "catalog", "quotes", "users", "audit"
    descripcion = Column(String(200), nullable=False)

class Rol(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)  # "superadmin", "admin", "comercial"
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    es_sistema = Column(Boolean, default=False, nullable=False)  # Si es True, no se puede eliminar

    permisos = relationship("Permiso", secondary=roles_permisos, backref="roles", lazy="joined")
