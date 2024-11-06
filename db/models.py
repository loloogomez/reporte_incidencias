from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from .client import Base

# Modelo para la tabla 'linea'
class Linea(Base):
    __tablename__ = "linea"

    id_linea = Column(Integer, primary_key=True, autoincrement=True)
    nombre_linea = Column(String(50), unique=True, nullable=False)

    # Relaciones
    estaciones = relationship("Estacion", back_populates="linea")
    usuarios = relationship("Usuario", back_populates="linea")

# Modelo para la tabla 'equipamiento'
class Equipamiento(Base):
    __tablename__ = "equipamiento"

    id_equipamiento = Column(Integer, primary_key=True, autoincrement=True)
    numero_chasis = Column(String(25), nullable=False)
    ubicacion = Column(String(25), nullable=False)
    tipo_equipamiento = Column(String(25), nullable=False)
    id_estacion_asociada = Column(Integer, ForeignKey("estacion.id_estacion"), nullable=False)

    # Relaciones
    estacion = relationship("Estacion", back_populates="equipamientos")
    incidencias = relationship("Incidencia", back_populates="equipamiento")

# Modelo para la tabla 'estacion'
class Estacion(Base):
    __tablename__ = "estacion"

    id_estacion = Column(Integer, primary_key=True, autoincrement=True)
    nombre_estacion = Column(String(50), unique=True, nullable=False)
    id_linea_asociada = Column(Integer, ForeignKey("linea.id_linea"), nullable=False)

    # Relaciones
    linea = relationship("Linea", back_populates="estaciones")
    equipamientos = relationship("Equipamiento", back_populates="estacion")

# Modelo para la tabla 'incidencia'
class Incidencia(Base):
    __tablename__ = "incidencia"

    id_incidencia = Column(Integer, primary_key=True, autoincrement=True)
    fecha_reclamo = Column(DateTime, nullable=False)
    fecha_finalizacion = Column(DateTime, nullable=True)
    prioridad = Column(String(25), nullable=False)
    flag = Column(String(15), nullable=False)
    tipo_problema = Column(String(50), nullable=False)
    descripcion = Column(String(250), nullable=True)
    tipo_resolucion = Column(String(250), nullable=True)
    id_cliente = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_tecnico_asignado = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=True)
    id_equipamiento = Column(Integer, ForeignKey("equipamiento.id_equipamiento"), nullable=False)

    # Relaciones
    cliente = relationship("Usuario", foreign_keys=[id_cliente], back_populates="incidencias_cliente")
    tecnico = relationship("Usuario", foreign_keys=[id_tecnico_asignado], back_populates="incidencias_tecnico")
    equipamiento = relationship("Equipamiento", back_populates="incidencias")

# Modelo para la tabla 'usuario'
class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    nombre_usuario = Column(String(50), unique=True, nullable=False)
    password = Column(String(60), nullable=False)
    mail = Column(String(50), unique=True, nullable=False)
    role = Column(String(20), nullable=False)  # Definir rol (cliente, técnico, etc.)
    telefono = Column(String(50), nullable=True)
    id_linea_asociada = Column(Integer, ForeignKey("linea.id_linea"), nullable=False)

    # Relaciones
    linea = relationship("Linea", back_populates="usuarios")
    incidencias_cliente = relationship("Incidencia", back_populates="cliente", foreign_keys="[Incidencia.id_cliente]")
    incidencias_tecnico = relationship("Incidencia", back_populates="tecnico", foreign_keys="[Incidencia.id_tecnico_asignado]")
