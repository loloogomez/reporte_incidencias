from fastapi import APIRouter, HTTPException, Depends
from db import schemas, models
from db.client import SessionLocal
from sqlalchemy.orm import Session

router = APIRouter(prefix="/cliente_molinetes", tags=["cliente_molinetes"], responses={404: {"message": "No encontrado"}})

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Obtener todos los clientes
@router.get("/", response_model=list[schemas.ClienteMolinetes], status_code=200)
async def get_clientes(db: Session = Depends(get_db)):
    return db.query(models.ClienteMolinetes).all()

# Obtener cliente por ID
@router.get("/{id_cliente}", response_model=schemas.ClienteMolinetes, status_code=200)
async def get_cliente(id_cliente: int, db: Session = Depends(get_db)):
    cliente = db.query(models.ClienteMolinetes).filter(models.ClienteMolinetes.id_cliente == id_cliente).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

# Crear nuevo cliente
@router.post("/", response_model=schemas.ClienteMolinetes, status_code=201)
async def create_cliente(cliente: schemas.ClienteMolinetesCreate, db: Session = Depends(get_db)):
    new_cliente = models.ClienteMolinetes(**cliente.dict())
    db.add(new_cliente)
    db.commit()
    db.refresh(new_cliente)
    return new_cliente

# Actualizar cliente por ID
@router.put("/{id_cliente}", response_model=schemas.ClienteMolinetes, status_code=200)
async def update_cliente(id_cliente: int, cliente: schemas.ClienteMolinetesUpdate, db: Session = Depends(get_db)):
    db_cliente = db.query(models.ClienteMolinetes).filter(models.ClienteMolinetes.id_cliente == id_cliente).first()
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    for key, value in cliente.dict(exclude_unset=True).items():
        setattr(db_cliente, key, value)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente

# Eliminar cliente por ID
@router.delete("/{id_cliente}", status_code=204)
async def delete_cliente(id_cliente: int, db: Session = Depends(get_db)):
    db_cliente = db.query(models.ClienteMolinetes).filter(models.ClienteMolinetes.id_cliente == id_cliente).first()
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    db.delete(db_cliente)
    db.commit()
    return {"message": "Cliente eliminado"}
