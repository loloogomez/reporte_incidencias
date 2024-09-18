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
    clientes = relationship("ClienteMolinetes", back_populates="linea")
    tecnicos = relationship("TecnicoMolinetes", back_populates="linea")

# Modelo para la tabla 'cliente_molinetes'
class ClienteMolinetes(Base):
    __tablename__ = "cliente_molinetes"

    id_cliente = Column(Integer, primary_key=True, autoincrement=True)
    nombre_usuario = Column(String(50), unique=True, nullable=False)
    telefono = Column(String(50), nullable=True)
    mail = Column(String(50), nullable=True)
    password = Column(String(50), nullable=False)
    id_linea_asociada = Column(Integer, ForeignKey("linea.id_linea"), nullable=False)

    # Relaciones
    linea = relationship("Linea", back_populates="clientes")
    incidencias = relationship("Incidencia", back_populates="cliente")

# Modelo para la tabla 'equipamiento'
class Equipamiento(Base):
    __tablename__ = "equipamiento"

    id_equipamiento = Column(Integer, primary_key=True, autoincrement=True)
    numero_chasis = Column(String(25), unique=True, nullable=False)
    ubicacion = Column(String(25), nullable=False)
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
    id_cliente = Column(Integer, ForeignKey("cliente_molinetes.id_cliente"), nullable=False)
    id_tecnico_asignado = Column(Integer, ForeignKey("tecnico_molinetes.id_tecnico"), nullable=True)
    id_equipamiento = Column(Integer, ForeignKey("equipamiento.id_equipamiento"), nullable=False)

    # Relaciones
    cliente = relationship("ClienteMolinetes", back_populates="incidencias")
    tecnico = relationship("TecnicoMolinetes", back_populates="incidencias")
    equipamiento = relationship("Equipamiento", back_populates="incidencias")

# Modelo para la tabla 'tecnico_molinetes'
class TecnicoMolinetes(Base):
    __tablename__ = "tecnico_molinetes"

    id_tecnico = Column(Integer, primary_key=True, autoincrement=True)
    nombre_apellido = Column(String(50), nullable=False)
    telefono = Column(String(50), nullable=True)
    mail = Column(String(50), nullable=False)
    password = Column(String(50), nullable=False)
    id_linea_recurrente = Column(Integer, ForeignKey("linea.id_linea"), nullable=False)

    # Relaciones
    linea = relationship("Linea", back_populates="tecnicos")
    incidencias = relationship("Incidencia", back_populates="tecnico")
