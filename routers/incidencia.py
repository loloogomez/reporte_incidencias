from fastapi import APIRouter, HTTPException, Depends
from db import schemas, models
from db.client import SessionLocal
from sqlalchemy.orm import Session
from datetime import datetime
from routers.auth import get_current_user

router = APIRouter(prefix="/incidencia", tags=["incidencia"], responses={404: {"message": "No encontrado"}}, dependencies=[Depends(get_current_user)])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Obtener todas las incidencias
@router.get("/", response_model=list[schemas.Incidencia], status_code=200)
async def get_incidencias(db: Session = Depends(get_db)):
    return db.query(models.Incidencia).all()

# Obtener incidencia por ID
@router.get("/{id_incidencia}", response_model=schemas.Incidencia, status_code=200)
async def get_incidencia(id_incidencia: int, db: Session = Depends(get_db)):
    incidencia = db.query(models.Incidencia).filter(models.Incidencia.id_incidencia == id_incidencia).first()
    if not incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    return incidencia

# Obtener incidencias por línea
@router.get("/linea/{id_linea}", response_model=list[schemas.Incidencia], status_code=200)
async def get_incidencias_por_linea(id_linea: int, db: Session = Depends(get_db)):
    
     # Verificar si el id de la linea asociada es valido
    db_linea = db.query(models.Linea).filter(models.Linea.id_linea == id_linea).first()
    
    if not db_linea:
        raise HTTPException(status_code=404, detail="Línea asociada no encontrada")
    
    incidencias = (
        db.query(models.Incidencia)
        .join(models.Equipamiento)
        .join(models.Estacion)
        .filter(models.Estacion.id_linea_asociada == id_linea)
        .all()
    )
    if not incidencias:
        raise HTTPException(status_code=404, detail="No se encontraron incidencias para la línea especificada")
    return incidencias

# Crear nueva incidencia
@router.post("/", response_model=schemas.Incidencia, status_code=201)
async def create_incidencia(incidencia: schemas.IncidenciaCreate, db: Session = Depends(get_db)):

    if incidencia.id_tecnico_asignado:
        db_tecnico = db.query(models.Usuario).filter(models.Usuario.id_usuario == incidencia.id_tecnico_asignado).first()
        if not db_tecnico:
            raise HTTPException(status_code=404, detail="Técnico no encontrado")

    db_cliente = db.query(models.Usuario).filter(models.Usuario.id_usuario == incidencia.id_cliente).first()
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    db_equipamiento = db.query(models.Equipamiento).filter(models.Equipamiento.id_equipamiento == incidencia.id_equipamiento).first()
    if not db_equipamiento:
        raise HTTPException(status_code=404, detail="Equipamiento no encontrado")
    
    incidencia.fecha_reclamo = datetime.now()

    new_incidencia = models.Incidencia(**incidencia.dict())
    db.add(new_incidencia)
    db.commit()
    db.refresh(new_incidencia)
    return new_incidencia

# Actualizar incidencia por ID
@router.put("/{id_incidencia}", response_model=schemas.Incidencia, status_code=200)
async def update_incidencia(id_incidencia: int, incidencia: schemas.IncidenciaUpdate, db: Session = Depends(get_db)):
    db_incidencia = db.query(models.Incidencia).filter(models.Incidencia.id_incidencia == id_incidencia).first()
    if not db_incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    if incidencia.id_tecnico_asignado:
        db_tecnico = db.query(models.Usuario).filter(models.TecnicoMolinetes.id_tecnico == incidencia.id_tecnico_asignado).first()
        if not db_tecnico:
            raise HTTPException(status_code=404, detail="Técnico no encontrado")

    db_cliente = db.query(models.Usuario).filter(models.Usuario.id_usuario == incidencia.id_cliente).first()
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    db_equipamiento = db.query(models.Equipamiento).filter(models.Equipamiento.id_equipamiento == incidencia.id_equipamiento).first()
    if not db_equipamiento:
        raise HTTPException(status_code=404, detail="Equipamiento no encontrado")
    
    for key, value in incidencia.dict(exclude_unset=True).items():
        setattr(db_incidencia, key, value)
    db.commit()
    db.refresh(db_incidencia)
    return db_incidencia

# Eliminar incidencia por ID
@router.delete("/{id_incidencia}", status_code=204)
async def delete_incidencia(id_incidencia: int, db: Session = Depends(get_db)):
    db_incidencia = db.query(models.Incidencia).filter(models.Incidencia.id_incidencia == id_incidencia).first()
    if not db_incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    db.delete(db_incidencia)
    db.commit()
    return {"message": "Incidencia eliminada"}
