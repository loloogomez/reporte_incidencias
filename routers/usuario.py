from fastapi import APIRouter, HTTPException, Depends
from db import schemas, models
from db.client import SessionLocal
from sqlalchemy.orm import Session
from routers.auth import get_password_hash, get_current_user
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/usuario", tags=["usuario"], responses={404: {"message": "No encontrado"}})

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Obtener todos los Usuarios
@router.get("/", response_model=list[schemas.Usuario], status_code=200)
async def get_users(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(models.Usuario).all()

# Obtener todos los Usuarios
@router.get("/tecnico", response_model=list[schemas.Usuario], status_code=200)
async def get_users(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(models.Usuario).filter(models.Usuario.role == "tecnico").all()

# Obtener Usuario por ID
@router.get("/{id_usuario}", response_model=schemas.Usuario, status_code=200)
async def get_Usuario(id_usuario: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

# Crear nuevo Usuario
@router.post("/", response_model=schemas.Usuario, status_code=201)
async def create_Usuario(Usuario: schemas.UsuarioCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):

    # Verificar si el id de la linea asociada es valido
    db_linea = db.query(models.Linea).filter(models.Linea.id_linea == Usuario.id_linea_asociada).first()
    
    if not db_linea:
        raise HTTPException(status_code=404, detail="Linea asociada no encontrada")
    
    # Verificar si ya existe una Usuario con el mismo nombre de usuario
    existing_Usuario = db.query(models.Usuario).filter(models.Usuario.nombre_usuario == Usuario.nombre_usuario).first()
    if existing_Usuario:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

    # encriptar la clave
    Usuario.password = get_password_hash(Usuario.password)

    new_Usuario = models.Usuario(**Usuario.dict())
    db.add(new_Usuario)
    db.commit()
    db.refresh(new_Usuario)
    return new_Usuario

# Actualizar Usuario por ID
@router.put("/{id_usuario}", response_model=schemas.Usuario, status_code=200)
async def update_Usuario(id_usuario: int, Usuario: schemas.UsuarioUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_Usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == id_usuario).first()
    if not db_Usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar si ya existe un Usuario con el mismo nombre de usuario
    existing_Usuario = db.query(models.Usuario).filter(models.Usuario.nombre_usuario == Usuario.nombre_usuario).first()
    
    if existing_Usuario and existing_Usuario.id_usuario != id_usuario:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

    # Verificar si el id de la linea asociada es valido
    db_linea = db.query(models.Linea).filter(models.Linea.id_linea == Usuario.id_linea_asociada).first()
    
    if not db_linea:
        raise HTTPException(status_code=404, detail="Línea asociada no encontrada")

    # encriptar la clave
    if Usuario.password:
        Usuario.password = get_password_hash(Usuario.password)

    for key, value in Usuario.dict(exclude_unset=True).items():
        setattr(db_Usuario, key, value)
    db.commit()
    db.refresh(db_Usuario)
    return db_Usuario

# Eliminar Usuario por ID
@router.delete("/{id_usuario}", status_code=204)
async def delete_Usuario(id_usuario: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_Usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == id_usuario).first()
    if not db_Usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(db_Usuario)
    db.commit()
    return {"message": "Usuario eliminado"}
