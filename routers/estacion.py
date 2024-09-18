from fastapi import APIRouter, HTTPException, Depends
from db import schemas, models
from db.client import SessionLocal
from sqlalchemy.orm import Session

router = APIRouter(prefix="/estacion", tags=["estacion"], responses={404: {"message": "No encontrado"}})

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Obtener todas las estaciones
@router.get("/", response_model=list[schemas.Estacion], status_code=200)
async def get_estaciones(db: Session = Depends(get_db)):
    return db.query(models.Estacion).all()

# Obtener estación por ID
@router.get("/{id_estacion}", response_model=schemas.Estacion, status_code=200)
async def get_estacion(id_estacion: int, db: Session = Depends(get_db)):
    estacion = db.query(models.Estacion).filter(models.Estacion.id_estacion == id_estacion).first()
    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    return estacion

# Crear nueva estación
@router.post("/", response_model=schemas.Estacion, status_code=201)
async def create_estacion(estacion: schemas.EstacionCreate, db: Session = Depends(get_db)):
    new_estacion = models.Estacion(**estacion.dict())
    db.add(new_estacion)
    db.commit()
    db.refresh(new_estacion)
    return new_estacion

# Actualizar estación por ID
@router.put("/{id_estacion}", response_model=schemas.Estacion, status_code=200)
async def update_estacion(id_estacion: int, estacion: schemas.EstacionUpdate, db: Session = Depends(get_db)):
    db_estacion = db.query(models.Estacion).filter(models.Estacion.id_estacion == id_estacion).first()
    if not db_estacion:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    for key, value in estacion.dict(exclude_unset=True).items():
        setattr(db_estacion, key, value)
    db.commit()
    db.refresh(db_estacion)
    return db_estacion

# Eliminar estación por ID
@router.delete("/{id_estacion}", status_code=204)
async def delete_estacion(id_estacion: int, db: Session = Depends(get_db)):
    db_estacion = db.query(models.Estacion).filter(models.Estacion.id_estacion == id_estacion).first()
    if not db_estacion:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    db.delete(db_estacion)
    db.commit()
    return {"message": "Estación eliminada"}
