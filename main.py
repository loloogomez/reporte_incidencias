from fastapi import FastAPI
from routers import auth, equipamiento, estacion, incidencia, linea, usuario
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Allows all origins from the list
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

app.include_router(auth.router)
app.include_router(equipamiento.router)
app.include_router(estacion.router)
app.include_router(incidencia.router)
app.include_router(linea.router)
app.include_router(usuario.router)
