from fastapi import FastAPI
from routers import cliente_molinetes, equipamiento, estacion, incidencia, linea, tecnico_molinetes

app = FastAPI()

app.include_router(cliente_molinetes.router)
app.include_router(equipamiento.router)
app.include_router(estacion.router)
app.include_router(incidencia.router)
app.include_router(linea.router)
app.include_router(tecnico_molinetes.router)
