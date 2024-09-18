from fastapi import APIRouter, HTTPException, Depends
from db import schemas, models
from db.client import SessionLocal
from sqlalchemy.orm import Session

router = APIRouter(prefix="/linea", tags=["linea"], responses={404: {"message": "No encontrado"}})

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Obtener todas las líneas
@router.get("/", response_model=list[schemas.Linea], status_code=200)
async def get_lineas(db: Session = Depends(get_db)):
    return db.query(models.Linea).all()

# Obtener línea por ID
@router.get("/{id_linea}", response_model=schemas.Linea, status_code=200)
async def get_linea(id_linea: int, db: Session = Depends(get_db)):
    linea = db.query(models.Linea).filter(models.Linea.id_linea == id_linea).first()
    if not linea:
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    return linea

# Crear nueva línea
@router.post("/", response_model=schemas.Linea, status_code=201)
async def create_linea(linea: schemas.LineaCreate, db: Session = Depends(get_db)):
    
    # Verificar si ya existe una línea con el mismo nombre
    existing_linea = db.query(models.Linea).filter(models.Linea.nombre_linea == linea.nombre_linea).first()
    if existing_linea:
        raise HTTPException(status_code=400, detail="El nombre de la línea ya existe")
    
    new_linea = models.Linea(**linea.dict())
    db.add(new_linea)
    db.commit()
    db.refresh(new_linea)
    return new_linea

# Actualizar línea por ID
@router.put("/{id_linea}", response_model=schemas.Linea, status_code=200)
async def update_linea(id_linea: int, linea: schemas.LineaUpdate, db: Session = Depends(get_db)):
    
    db_linea = db.query(models.Linea).filter(models.Linea.id_linea == id_linea).first()
    
    if not db_linea:
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    
    # Verificar si ya existe otra línea con el mismo nombre
    existing_linea = db.query(models.Linea).filter(models.Linea.nombre_linea == linea.nombre_linea).first()

    # Asegurarse de que no sea la misma línea (en caso de que el nombre no haya cambiado)
    if existing_linea and existing_linea.id_linea != id_linea:
        raise HTTPException(status_code=400, detail="El nombre de la línea ya está en uso por otra línea")

    for key, value in linea.dict(exclude_unset=True).items():
        setattr(db_linea, key, value)
    db.commit()
    db.refresh(db_linea)
    return db_linea

# Eliminar línea por ID
@router.delete("/{id_linea}", status_code=204)
async def delete_linea(id_linea: int, db: Session = Depends(get_db)):
    db_linea = db.query(models.Linea).filter(models.Linea.id_linea == id_linea).first()
    if not db_linea:
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    db.delete(db_linea)
    db.commit()
    return {"message": "Línea eliminada"}
