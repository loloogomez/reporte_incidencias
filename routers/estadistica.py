from fastapi import APIRouter, HTTPException, Depends, Query
from db import schemas, models
from db.client import SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import extract
from routers.auth import get_current_user
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from io import BytesIO
from fastapi.responses import StreamingResponse
from collections import Counter


router = APIRouter(prefix="/estadistica", tags=["estadistica"], responses={404: {"message": "No encontrado"}})

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/incidencias", status_code=200)
async def obtener_estadisticas_incidentes(
    mes: int = Query(..., ge=1, le=12, description="Mes del año"),
    anio: int = Query(..., ge=2023, le=2100, description="Año"),
    db: Session = Depends(get_db)
):
    # Filtrar incidencias del mes y año proporcionado
    incidencias = (
        db.query(models.Incidencia)
        .join(models.Equipamiento)
        .join(models.Estacion)
        .join(models.Linea)
        .filter(
            extract('month', models.Incidencia.fecha_reclamo) == mes,
            extract('year', models.Incidencia.fecha_reclamo) == anio
        )
        .filter(models.Incidencia.flag == "Finalizada")
        .all()
    )

    if not incidencias:
        raise HTTPException(status_code=404, detail="No hay incidencias registradas en este período.")

    # Procesar datos para gráficos
    datos_lineas = Counter([
        inc.equipamiento.estacion.linea.nombre_linea
        for inc in incidencias
        if inc.equipamiento and inc.equipamiento.estacion and inc.equipamiento.estacion.linea
    ])
    datos_equipos = Counter([inc.equipamiento.tipo_equipamiento for inc in incidencias])
    vandalismos = [inc for inc in incidencias if inc.tipo_problema == "Vandalismo"]
    
    # Contar incidencias por tipo de avería
    tipos_averia = Counter([inc.tipo_problema for inc in incidencias])

    # Configurar la cantidad de gráficos
    num_graficos = 4
    fig, axs = plt.subplots(1, num_graficos, figsize=(5 * num_graficos, 5))
    axs = axs if num_graficos > 1 else [axs]

    # Gráfico 1: Incidencias por línea
    axs[0].bar(datos_lineas.keys(), datos_lineas.values(), color="blue")
    axs[0].set_title("Incidencias por Línea")
    axs[0].set_ylabel("Cantidad")
    axs[0].yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x)}'))

    # Gráfico 2: Porcentaje por tipo de equipamiento
    axs[1].pie(datos_equipos.values(), labels=datos_equipos.keys(), autopct='%1.1f%%')
    axs[1].set_title("Porcentaje por Tipo de Equipamiento")

    # Gráfico 3: Resolución de vandalismos
    if vandalismos:
        vandalismos_resueltos = sum(1 for inc in vandalismos if inc.fecha_finalizacion)
        vandalismos_pendientes = len(vandalismos) - vandalismos_resueltos
        axs[2].bar(["Resueltos", "Pendientes"], [vandalismos_resueltos, vandalismos_pendientes], color=["green", "red"])
    else:
        axs[2].text(0.5, 0.5, "No hay datos", horizontalalignment='center', verticalalignment='center', fontsize=12)
    
    axs[2].set_title("Resolución de Vandalismos")
    axs[2].set_ylabel("Cantidad")
    axs[2].yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x)}'))
    
    # Gráfico 4: Porcentaje por tipo de avería (torta/rosquilla)
    axs[3].pie(tipos_averia.values(), labels=tipos_averia.keys(), autopct='%1.1f%%', startangle=90, wedgeprops={'width': 0.3})
    axs[3].set_title("Porcentaje por Tipo de Avería")
        
    # Guardar en un buffer
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="image/png")