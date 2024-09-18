from fastapi import APIRouter, HTTPException, Depends
from db import schemas, models
from db.client import SessionLocal
from sqlalchemy.orm import Session

router = APIRouter(prefix="/tecnico_molinetes", tags=["tecnico_molinetes"], responses={404: {"message": "No encontrado"}})

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Obtener todos los técnicos
@router.get("/", response_model=list[schemas.TecnicoMolinetes], status_code=200)
async def get_tecnicos(db: Session = Depends(get_db)):
    return db.query(models.TecnicoMolinetes).all()

# Obtener técnico por ID
@router.get("/{id_tecnico}", response_model=schemas.TecnicoMolinetes, status_code=200)
async def get_tecnico(id_tecnico: int, db: Session = Depends(get_db)):
    tecnico = db.query(models.TecnicoMolinetes).filter(models.TecnicoMolinetes.id_tecnico == id_tecnico).first()
    if not tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")
    return tecnico

# Crear nuevo técnico
@router.post("/", response_model=schemas.TecnicoMolinetes, status_code=201)
async def create_tecnico(tecnico: schemas.TecnicoMolinetesCreate, db: Session = Depends(get_db)):
    new_tecnico = models.TecnicoMolinetes(**tecnico.dict())
    db.add(new_tecnico)
    db.commit()
    db.refresh(new_tecnico)
    return new_tecnico

# Actualizar técnico por ID
@router.put("/{id_tecnico}", response_model=schemas.TecnicoMolinetes, status_code=200)
async def update_tecnico(id_tecnico: int, tecnico: schemas.TecnicoMolinetesUpdate, db: Session = Depends(get_db)):
    db_tecnico = db.query(models.TecnicoMolinetes).filter(models.TecnicoMolinetes.id_tecnico == id_tecnico).first()
    if not db_tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")
    for key, value in tecnico.dict(exclude_unset=True).items():
        setattr(db_tecnico, key, value)
    db.commit()
    db.refresh(db_tecnico)
    return db_tecnico

# Eliminar técnico por ID
@router.delete("/{id_tecnico}", status_code=204)
async def delete_tecnico(id_tecnico: int, db: Session = Depends(get_db)):
    db_tecnico = db.query(models.TecnicoMolinetes).filter(models.TecnicoMolinetes.id_tecnico == id_tecnico).first()
    if not db_tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")
    db.delete(db_tecnico)
    db.commit()
    return {"message": "Técnico eliminado"}
