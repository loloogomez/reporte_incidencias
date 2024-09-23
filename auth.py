from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from db.client import SessionLocal
from db import models

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Clave secreta para firmar los tokens
SECRET_KEY = "secretkey123456"  # Cambia por una clave más segura
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 5

# Simula un contexto de hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Ruta donde FastAPI espera el token de acceso
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Función para hashear contraseñas
def get_password_hash(password: str):
    return pwd_context.hash(password)

# Función para verificar contraseñas
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# Función para crear un JWT
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependencia para verificar el token
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        id_usuario: str = payload.get("sub")
        tipo_usuario: str = payload.get("tipo_usuario")
        if id_usuario is None or tipo_usuario is None:
            raise credentials_exception
        
        # Verificar el tipo de usuario
        if tipo_usuario == "cliente":
            user = db.query(models.ClienteMolinetes).filter(models.ClienteMolinetes.id_cliente == id_usuario).first()
        elif tipo_usuario == "tecnico":
            user = db.query(models.TecnicoMolinetes).filter(models.TecnicoMolinetes.id_tecnico == id_usuario).first()
        else:
            raise credentials_exception
        
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return user

