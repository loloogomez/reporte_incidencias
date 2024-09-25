from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

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


# Esquema para 'ClienteMolinetes'
class ClienteMolinetesBase(BaseModel):
    nombre_usuario: str = Field(..., max_length=50)
    telefono: Optional[str] = Field(None, max_length=50)
    mail: Optional[str] = Field(None, max_length=50)
    id_linea_asociada: int

class ClienteMolinetesCreate(ClienteMolinetesBase):
    password: str = Field(..., max_length=60)

class ClienteMolinetesUpdate(ClienteMolinetesBase):
    password: str = Field(..., max_length=60)
class ClienteMolinetes(ClienteMolinetesBase):
    id_cliente: int

    class Config:
        from_attributes = True

# Esquema para 'Equipamiento'
class EquipamientoBase(BaseModel):
    numero_chasis: str = Field(..., max_length=25)
    ubicacion: str = Field(..., max_length=25)
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

# Esquema para 'TecnicoMolinetes'
class TecnicoMolinetesBase(BaseModel):
    nombre_apellido: str = Field(..., max_length=50)
    telefono: Optional[str] = Field(None, max_length=50)
    mail: str = Field(None, max_length=50)
    id_linea_recurrente: int
    dni: int

class TecnicoMolinetesCreate(TecnicoMolinetesBase):
    password: str = Field(..., max_length=60)

class TecnicoMolinetesUpdate(TecnicoMolinetesBase):
    password: str = Field(..., max_length=60)

class TecnicoMolinetes(TecnicoMolinetesBase):
    id_tecnico: int

    class Config:
        from_attributes = True