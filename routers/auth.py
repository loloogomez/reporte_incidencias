from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from db.client import SessionLocal
from db import models

router = APIRouter(prefix="/auth", tags=["auth"], responses={404: {"message": "No encontrado"}})

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
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
    
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
        
        user = db.query(models.Usuario).filter(models.Usuario.id_usuario == id_usuario).first()
        
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return user

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        
        username: str = payload.get("sub", None)
        if username is None:
            raise HTTPException(status_code=403, detail="Token is invalid or expired")
        
        rol: str = payload.get("tipo_usuario", None)
        if rol is None:
            raise HTTPException(status_code=403, detail="Token is invalid or expired")
        
        return payload
    except JWTError:
        raise HTTPException(status_code=403, detail="Token is invalid or expired")

# Endpoint para iniciar sesión
@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):  
    user = db.query(models.Usuario).filter(models.Usuario.nombre_usuario == form_data.username).first()

    # Verificar credenciales
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Si las credenciales son válidas, generar el token
    access_token = create_access_token(data={"sub": str(user.id_usuario), "tipo_usuario": user.role})
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/get_role/{token}")
async def get_user_role(token: str, current_user = Depends(get_current_user)):
    role = verify_token(token).get("tipo_usuario")
    return {"role":role}

@router.get("/get_id_usuario/{token}")
async def get_user_role(token: str, current_user = Depends(get_current_user)):
    id_usuario = verify_token(token).get("sub")
    return {"id_usuario":id_usuario}

@router.get("/verify_token/{token}")
async def verify_user_token(token: str):
    verify_token(token)
    return {"message": "Token is valid"}