from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

# Definir el enum para roles de usuario
class RoleEnum(str, Enum):
    cliente = "cliente"
    tecnico = "tecnico"
    admin = "admin"

# Esquema Base para todos los usuarios (Cliente y Técnico)
class UsuarioBase(BaseModel):
    nombre_usuario: str = Field(..., max_length=50)
    telefono: Optional[str] = Field(None, max_length=50)
    mail: Optional[str] = Field(None, max_length=50)
    role: RoleEnum = Field(...)
    id_linea_asociada: int

class UsuarioCreate(UsuarioBase):
    password: str = Field(..., max_length=60)

class UsuarioUpdate(UsuarioBase):
    password: Optional[str] = Field(None, max_length=60)

class Usuario(UsuarioBase):
    id_usuario: int

    class Config:
        from_attributes = True

# Esquema para 'Linea'
class LineaBase(BaseModel):
    nombre_linea: str = Field(..., max_length=50)

class LineaCreate(LineaBase):
    pass

class LineaUpdate(LineaBase):
    pass

class Linea(LineaBase):
    id_linea: int

    class Config:
        from_attributes = True

# Esquema para 'Equipamiento'
class EquipamientoBase(BaseModel):
    numero_chasis: str = Field(..., max_length=25)
    ubicacion: str = Field(..., max_length=25)
    tipo_equipamiento: str = Field(..., max_length=25)  
    id_estacion_asociada: int

class EquipamientoCreate(EquipamientoBase):
    pass

class EquipamientoUpdate(EquipamientoBase):
    pass

class Equipamiento(EquipamientoBase):
    id_equipamiento: int

    class Config:
        from_attributes = True

# Esquema para 'Estacion'
class EstacionBase(BaseModel):
    nombre_estacion: str = Field(..., max_length=50)
    id_linea_asociada: int

class EstacionCreate(EstacionBase):
    pass

class EstacionUpdate(EstacionBase):
    pass

class Estacion(EstacionBase):
    id_estacion: int

    class Config:
        from_attributes = True

# Esquema para 'Incidencia'
class IncidenciaBase(BaseModel):
    fecha_reclamo: Optional[datetime] = None
    fecha_finalizacion: Optional[datetime] = None
    prioridad: str = Field(..., max_length=25)
    flag: str = Field(..., max_length=15)
    tipo_problema: str = Field(..., max_length=50)
    descripcion: Optional[str] = Field(None, max_length=250)
    tipo_resolucion: Optional[str] = Field(None, max_length=250)
    id_cliente: int
    id_tecnico_asignado: Optional[int] = None
    id_equipamiento: int

class IncidenciaCreate(IncidenciaBase):
    pass

class IncidenciaUpdate(IncidenciaBase):
    pass

class Incidencia(IncidenciaBase):
    id_incidencia: int

    class Config:
        from_attributes = True
        
class IncidenciaCompleta(BaseModel):
    id_incidencia: int
    fecha_reclamo: datetime
    fecha_finalizacion: Optional[datetime] = None
    prioridad: str = Field(..., max_length=25)
    flag: str = Field(..., max_length=15)
    tipo_problema: str = Field(..., max_length=50)
    descripcion: Optional[str] = Field(None, max_length=250)
    tipo_resolucion: Optional[str] = Field(None, max_length=250)
    nombre_cliente: str  # Nombre del cliente
    nombre_tecnico: Optional[str] = None # Nombre del técnico, puede ser None
    chasis: str = Field(..., max_length=25)
    tipo_equipamiento: str = Field(..., max_length=25)
    nombre_estacion: str = Field(..., max_length=50)
    nombre_linea: str = Field(..., max_length=50)

    class Config:
        from_attributes = True
        
class TipoResolucion(BaseModel):
    tipo_resolucion: str