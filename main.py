from fastapi import FastAPI
from routers import auth, equipamiento, estacion, incidencia, linea, usuario

app = FastAPI()

app.include_router(auth.router)
app.include_router(equipamiento.router)
app.include_router(estacion.router)
app.include_router(incidencia.router)
app.include_router(linea.router)
app.include_router(usuario.router)
