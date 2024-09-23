from fastapi import APIRouter, HTTPException, Depends
from db import schemas, models
from db.client import SessionLocal
from sqlalchemy.orm import Session
from auth import create_access_token, verify_password, get_current_user, get_password_hash
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/tecnico_molinetes", tags=["tecnico_molinetes"], responses={404: {"message": "No encontrado"}})

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint para iniciar sesión
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.TecnicoMolinetes).filter(models.TecnicoMolinetes.dni == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Si las credenciales son válidas, generamos un token
    access_token = create_access_token(data={"sub": user.id_tecnico, "tipo_usuario":"tecnico"})
    return {"access_token": access_token, "token_type": "bearer"}

# Obtener todos los técnicos
@router.get("/", response_model=list[schemas.TecnicoMolinetes], status_code=200)
async def get_tecnicos(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(models.TecnicoMolinetes).all()

# Obtener técnico por ID
@router.get("/{id_tecnico}", response_model=schemas.TecnicoMolinetes, status_code=200)
async def get_tecnico(id_tecnico: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    tecnico = db.query(models.TecnicoMolinetes).filter(models.TecnicoMolinetes.id_tecnico == id_tecnico).first()
    if not tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")
    return tecnico

# Crear nuevo técnico
@router.post("/", response_model=schemas.TecnicoMolinetes, status_code=201)
async def create_tecnico(tecnico: schemas.TecnicoMolinetesCreate, db: Session = Depends(get_db)):
    
    # Verificar si el id de la linea asociada es valido
    db_linea = db.query(models.Linea).filter(models.Linea.id_linea == tecnico.id_linea_recurrente).first()
    
    if not db_linea:
        raise HTTPException(status_code=404, detail="Linea recurrente no encontrada")
    
    # Verificar si ya existe una tecnico con el mismo nombre de usuario
    existing_tecnico = db.query(models.TecnicoMolinetes).filter(models.TecnicoMolinetes.mail == tecnico.mail).first()
    if existing_tecnico:
        raise HTTPException(status_code=400, detail="El mail ya existe")

    # encriptar la clave
    tecnico.password =  get_password_hash(tecnico.password)
    
    new_tecnico = models.TecnicoMolinetes(**tecnico.dict())
    db.add(new_tecnico)
    db.commit()
    db.refresh(new_tecnico)
    return new_tecnico

# Actualizar técnico por ID
@router.put("/{id_tecnico}", response_model=schemas.TecnicoMolinetes, status_code=200)
async def update_tecnico(id_tecnico: int, tecnico: schemas.TecnicoMolinetesUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_tecnico = db.query(models.TecnicoMolinetes).filter(models.TecnicoMolinetes.id_tecnico == id_tecnico).first()
    if not db_tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")
    
    # Verificar si el id de la linea asociada es valido
    db_linea = db.query(models.Linea).filter(models.Linea.id_linea == tecnico.id_linea_recurrente).first()
    
    if not db_linea:
        raise HTTPException(status_code=404, detail="Linea recurrente no encontrada")
    
    # Verificar si ya existe una tecnico con el mismo nombre de usuario
    existing_tecnico = db.query(models.TecnicoMolinetes).filter(models.TecnicoMolinetes.mail == tecnico.mail).first()
    if existing_tecnico and existing_tecnico.id_tecnico != id_tecnico:
        raise HTTPException(status_code=400, detail="El mail ya existe")

    # encriptar la clave
    tecnico.password = crypt.hash(tecnico.password)

    for key, value in tecnico.dict(exclude_unset=True).items():
        setattr(db_tecnico, key, value)
    db.commit()
    db.refresh(db_tecnico)
    return db_tecnico

# Eliminar técnico por ID
@router.delete("/{id_tecnico}", status_code=204)
async def delete_tecnico(id_tecnico: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_tecnico = db.query(models.TecnicoMolinetes).filter(models.TecnicoMolinetes.id_tecnico == id_tecnico).first()
    if not db_tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")
    db.delete(db_tecnico)
    db.commit()
    return {"message": "Técnico eliminado"}
