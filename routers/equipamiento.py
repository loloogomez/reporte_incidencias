from fastapi import APIRouter, HTTPException, Depends
from db import schemas, models
from db.client import SessionLocal
from sqlalchemy.orm import Session

router = APIRouter(prefix="/equipamiento", tags=["equipamiento"], responses={404: {"message": "No encontrado"}})

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Obtener todos los equipamientos
@router.get("/", response_model=list[schemas.Equipamiento], status_code=200)
async def get_equipamientos(db: Session = Depends(get_db)):
    return db.query(models.Equipamiento).all()

# Obtener equipamiento por ID
@router.get("/{id_equipamiento}", response_model=schemas.Equipamiento, status_code=200)
async def get_equipamiento(id_equipamiento: int, db: Session = Depends(get_db)):
    equipamiento = db.query(models.Equipamiento).filter(models.Equipamiento.id_equipamiento == id_equipamiento).first()
    if not equipamiento:
        raise HTTPException(status_code=404, detail="Equipamiento no encontrado")
    return equipamiento

# Crear nuevo equipamiento
@router.post("/", response_model=schemas.Equipamiento, status_code=201)
async def create_equipamiento(equipamiento: schemas.EquipamientoCreate, db: Session = Depends(get_db)):
    new_equipamiento = models.Equipamiento(**equipamiento.dict())
    db.add(new_equipamiento)
    db.commit()
    db.refresh(new_equipamiento)
    return new_equipamiento

# Actualizar equipamiento por ID
@router.put("/{id_equipamiento}", response_model=schemas.Equipamiento, status_code=200)
async def update_equipamiento(id_equipamiento: int, equipamiento: schemas.EquipamientoUpdate, db: Session = Depends(get_db)):
    db_equipamiento = db.query(models.Equipamiento).filter(models.Equipamiento.id_equipamiento == id_equipamiento).first()
    if not db_equipamiento:
        raise HTTPException(status_code=404, detail="Equipamiento no encontrado")
    for key, value in equipamiento.dict(exclude_unset=True).items():
        setattr(db_equipamiento, key, value)
    db.commit()
    db.refresh(db_equipamiento)
    return db_equipamiento

# Eliminar equipamiento por ID
@router.delete("/{id_equipamiento}", status_code=204)
async def delete_equipamiento(id_equipamiento: int, db: Session = Depends(get_db)):
    db_equipamiento = db.query(models.Equipamiento).filter(models.Equipamiento.id_equipamiento == id_equipamiento).first()
    if not db_equipamiento:
        raise HTTPException(status_code=404, detail="Equipamiento no encontrado")
    db.delete(db_equipamiento)
    db.commit()
    return {"message": "Equipamiento eliminado"}
