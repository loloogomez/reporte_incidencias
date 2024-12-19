from datetime import datetime
from fastapi.responses import HTMLResponse
from fastapi import APIRouter, HTTPException, Depends, Query
from db import models
from db.client import SessionLocal
from sqlalchemy.orm import Session
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import numpy as np

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
    fecha_desde: str = Query(..., description="Fecha inicial (YYYY-MM-DD)"),
    fecha_hasta: str = Query(..., description="Fecha final (YYYY-MM-DD)"),
    graficos: str = Query(..., description="Gráficos a generar separados por comas"),
    db: Session = Depends(get_db)
):
    # Convertir las fechas a objetos datetime
    try:
        fecha_desde_dt = datetime.strptime(fecha_desde, "%Y-%m-%d")
        fecha_hasta_dt = datetime.strptime(fecha_hasta, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD.")

    # Convertir la lista de gráficos a generar
    graficos_solicitados = graficos.split(",")

    # Filtrar incidencias entre las fechas proporcionadas
    incidencias = (
        db.query(
            models.Incidencia.tipo_problema,
            models.Linea.nombre_linea,
            models.Estacion.nombre_estacion,
            models.Incidencia.fecha_reclamo,
            models.Incidencia.fecha_finalizacion,
            models.Incidencia.prioridad,
        )
        .join(models.Equipamiento, models.Incidencia.id_equipamiento == models.Equipamiento.id_equipamiento)
        .join(models.Estacion, models.Equipamiento.id_estacion_asociada == models.Estacion.id_estacion)
        .join(models.Linea, models.Estacion.id_linea_asociada == models.Linea.id_linea)
        .filter(models.Incidencia.fecha_reclamo.between(fecha_desde_dt, fecha_hasta_dt))
        .filter(models.Incidencia.flag == "Finalizada")
        .all()
    )

    if not incidencias:
        raise HTTPException(status_code=404, detail="No se encontraron incidencias en este período.")

    # Convertir resultados a DataFrame
    columnas = ["tipo_problema", "nombre_linea", "nombre_estacion", "fecha_reclamo", "fecha_finalizacion", "prioridad"]
    datos_df = pd.DataFrame(incidencias, columns=columnas)
    
    datos_df["tiempo_resolucion"] = (datos_df["fecha_finalizacion"] - datos_df["fecha_reclamo"]).dt.days

    # Contenedor para HTML de gráficos
    html_content = "<html><head><title>Gráficos Solicitados</title></head><body>"

    # Treemap
    if "treemap" in graficos_solicitados:
        treemap_fig = px.treemap(
            datos_df,
            path=["nombre_linea", "nombre_estacion", "tipo_problema"],
            title=f"Treemap: Incidencias por Línea, Estación y Tipo de Problema ({fecha_desde} a {fecha_hasta})",
            color="nombre_linea",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        treemap_html = treemap_fig.to_html(full_html=False)
        html_content += f"<h3>Treemap</h3>{treemap_html}"
        
    
    # Bubble Chart
    if "bubble_chart" in graficos_solicitados:            
        problema_count = datos_df.groupby(["nombre_linea", "tipo_problema", "nombre_estacion"]).size().reset_index(name="Cantidad")
        np.random.seed(42)
        problema_count['x'] = np.random.rand(len(problema_count))  # Coordenadas aleatorias para el eje X
        problema_count['y'] = np.random.rand(len(problema_count))  # Coordenadas aleatorias para el eje Y

        bubble_fig = px.scatter(
            problema_count,
            x="x",
            y="y",
            size="Cantidad",
            color="nombre_linea",
            hover_name="nombre_estacion",
            hover_data={"tipo_problema": True, "Cantidad": True},
            text="tipo_problema",
            size_max=120,
            title=f"Incidencias por Línea, Tipo de Problema y Estación desde:({fecha_desde}), hasta: ({fecha_hasta})"
        )
        bubble_fig.update_traces(marker=dict(opacity=0.8, line=dict(width=1, color="black")), textposition="middle center")
        bubble_html = bubble_fig.to_html(full_html=False)
        html_content += f"<h3>Bubble Chart</h3>{bubble_html}"
        
    
    # Gráfico de barras con diferenciación por rango
    if "tiempo_resolucion_barras" in graficos_solicitados:
        
        # Primero, asegurarnos que la columna "cumple_rango" tiene los valores correctos
        rangos_prioridad = {
            "Alta": (2, 6),  # Entre 2 a 6 horas
            "Media": (5, 12),  # Entre 5 a 12 horas
            "Baja": (24, 48),  # Entre 24 a 48 horas
            "Vandalismo": (5, 168)  # Entre 5 a 168 horas
        }

        # Calcular tiempo de resolución en horas
        datos_df["tiempo_resolucion_horas"] = datos_df["tiempo_resolucion"] * 24  # Convertir días a horas

        # Verificar si están dentro del rango
        def verificar_rango(prioridad, tiempo):
            if prioridad in rangos_prioridad:
                min_horas, max_horas = rangos_prioridad[prioridad]
                return "Dentro del Rango" if min_horas <= tiempo <= max_horas else "Fuera del Rango"
            return "Sin Rango Definido"

        datos_df["cumple_rango"] = datos_df.apply(
            lambda row: verificar_rango(row["prioridad"], row["tiempo_resolucion_horas"]), axis=1
        )
        
        # gráfico de barras con colores diferenciados
        barras_fig = px.histogram(
            datos_df,
            x="prioridad",
            color="cumple_rango",
            title=f"Cumplimiento de Tiempos de Resolución por Prioridad desde:{fecha_desde}, hasta: {fecha_hasta}",
            labels={"prioridad": "Prioridad", "cumple_rango": "Cumple con el Rango"},
            barmode="group",
            facet_col="nombre_linea",  # Separar por nombre_linea
            #facet_col_title="Linea",  # Cambiar el título de la faceta a "Linea"
            color_discrete_map={
                "Dentro del Rango": "green",  # Color para dentro del rango
                "Fuera del Rango": "red",    # Color para fuera del rango
                "Sin Rango Definido": "gray"  # Color para casos sin rango definido
            }
        )

        # Convertir el gráfico a HTML
        barras_html = barras_fig.to_html(full_html=False)    
    
        html_content += f"<h3>Barras</h3>{barras_html}"
        
        
    # Barras por tipo de incidencia
    if "tipo_incidencia_barra" in graficos_solicitados:
        # Resumir los datos por estación y tipo de problema
        resumen_lineas = datos_df.groupby(["nombre_linea", "tipo_problema"]).size().unstack(fill_value=1)

        # Crear una paleta de colores
        colores = sns.color_palette("pastel", n_colors=len(resumen_lineas.columns))

        # Crear el gráfico de barras apiladas
        plt.figure(figsize=(12, 8))
        resumen_lineas.plot(
            kind="bar", 
            stacked=True, 
            color=colores, 
            edgecolor="black"
        )

        # Etiquetas y título
        plt.xlabel("Lineas", fontsize=12)
        plt.ylabel("Cantidad de Incidencias", fontsize=12)
        plt.legend(title="Tipo de Incidencia", bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        # Guardar el gráfico como imagen base64
        with BytesIO() as buffer:
            plt.savefig(buffer, format="png")
            buffer.seek(0)
            barras_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        plt.close()

        # Añadir el gráfico al contenedor HTML
        barras_resumen_html = f"""
        <div>
            <h3>Cantidad de Incidencias por Linea y Tipo de Incidencia</h3>
            <img src="data:image/png;base64,{barras_base64}" style="width: 800px;">
        </div>
        """
        
        html_content += barras_resumen_html
        
    # Gráfico de torta tipo problema por linea
    if "torta_por_linea" in graficos_solicitados:
        pie_html_lineas = '<div style="display: flex; flex-wrap: wrap; gap: 30px;">'

        estaciones_unicas = datos_df["nombre_estacion"].unique()
        problemas_unicos = datos_df["tipo_problema"].unique()

        for linea in datos_df["nombre_linea"].unique():
            linea_df = datos_df[datos_df["nombre_linea"] == linea]
            
            # Resumir datos para el gráfico
            resumen = linea_df.groupby("tipo_problema").size().reset_index(name="Cantidad")
            total_incidencias = resumen["Cantidad"].sum()  # Cantidad total de incidencias
            colores = sns.color_palette("pastel")[:len(resumen["Cantidad"])]
            plt.figure(figsize=(7, 8))
            plt.pie(
                resumen["Cantidad"], 
                labels=resumen["tipo_problema"], 
                autopct=lambda p: f'{int(round(p * total_incidencias / 100))}',
                #autopct='%1.1f%%',    (descomentar si se quiere en porcentaje)
                startangle=140,
                colors=colores,
                wedgeprops={"linewidth": 1.5, "edgecolor": "white"}, frame=False
            )
            plt.title(f"Cantidad de incidencias en la Línea {linea} (Total: {total_incidencias})")
            plt.axis('equal')

            # Guardar gráfico como imagen base64
            with BytesIO() as buffer:
                plt.savefig(buffer, format="png")
                buffer.seek(0)
                linea_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            plt.close()

            # Añadir el gráfico al contenedor HTML
            pie_html_lineas += f'<div><h3>Línea: {linea}</h3><img src="data:image/png;base64,{linea_base64}" style="width: 300px;"></div>'

        pie_html_lineas += '</div>'
        html_content += pie_html_lineas
        
    # Volumen mensual por linea
    if "volumen_mensual_por_linea" in graficos_solicitados:
        # Crear una lista para almacenar los datos que exportaremos
        datos_exportacion = []

        linea_mes_html = ""
        estaciones_unicas = datos_df["nombre_linea"].unique()
        problemas_unicos = datos_df["tipo_problema"].unique()
        datos_df["fecha_reclamo"] = pd.to_datetime(datos_df["fecha_reclamo"])
        datos_df["mes_reclamo"] = datos_df["fecha_reclamo"].dt.month
        colores_lineas = sns.color_palette("pastel")[:len(problemas_unicos)]

        for estacion in estaciones_unicas:
            # Filtrar los datos para la estación actual
            estacion_df = datos_df[datos_df["nombre_linea"] == estacion]
            colores_lineas = sns.color_palette("pastel")[:len(problemas_unicos)]
            
            # Crear una nueva figura para cada estación
            fig, ax = plt.subplots(figsize=(12, 8))

            # Iterar sobre cada tipo de problema para graficarlos
            for i, problema in enumerate(problemas_unicos):
                # Filtrar los datos para el tipo de problema actual
                problema_df = estacion_df[estacion_df["tipo_problema"] == problema]
                
                # Contar la cantidad de problemas por mes
                problemas_por_mes = problema_df.groupby("mes_reclamo").size()
                
                # Asegurar que los meses faltantes tengan valor 0
                problemas_por_mes = problemas_por_mes.reindex(range(1, 13), fill_value=0)
                
                # Guardar los datos en la lista para exportar
                for mes, cantidad in problemas_por_mes.items():
                    datos_exportacion.append({
                        "nombre_linea": estacion,
                        "tipo_problema": problema,
                        "mes_finalizacion": mes,
                        "cantidad_problemas": cantidad
                    })
            
            # Graficar la línea
            ax.plot(
                problemas_por_mes.index, 
                problemas_por_mes.values, 
                label=f"{problema}",  # Solo el tipo de problema
                color=colores_lineas[i]
            )

            # Etiquetas y título para cada gráfico
            ax.set_title(f"Línea de Tiempo de Problemas - {estacion}", fontsize=16)
            ax.set_xlabel("Mes de Reclamo", fontsize=12)
            ax.set_ylabel("Cantidad de incidencias", fontsize=12)
            ax.set_xticks(range(1, 13))
            ax.set_xticklabels([
                "Ene", "Feb", "Mar", "Abr", "May", "Jun", 
                "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
            ])

            # Añadir una leyenda
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)

            # Ajustar el diseño para que no se sobrepongan los elementos
            plt.tight_layout()

            # Convertir la imagen a base64 y guardarla en HTML
            with BytesIO() as buffer:
                plt.savefig(buffer, format="png")
                buffer.seek(0)
                plot_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            # Cerrar el gráfico para liberar memoria
            plt.close()

            # Añadir el gráfico al HTML
            linea_mes_html += f"""
            <h2>Estación: {estacion}</h2>
            <img src="data:image/png;base64,{plot_base64}" alt="Gráfico de Problemas - {estacion}">
            """
        html_content += linea_mes_html
        
    # GRAFICO DIARIO
    if "volumen_diario_por_linea" in graficos_solicitados:
        linea_dia_html = ""
        estaciones_unicas = datos_df["nombre_linea"].unique()
        problemas_unicos = datos_df["tipo_problema"].unique()

        # Convertir la columna de fecha a formato datetime y extraer el día
        datos_df["fecha_reclamo"] = pd.to_datetime(datos_df["fecha_reclamo"])
        datos_df["dia_reclamo"] = datos_df["fecha_reclamo"].dt.day

        for estacion in estaciones_unicas:
            estacion_df = datos_df[datos_df["nombre_linea"] == estacion]
            colores_lineas = sns.color_palette("pastel")[:len(problemas_unicos)]

            # Crear una nueva figura para cada estación
            fig, ax = plt.subplots(figsize=(12, 8))

            # Iterar sobre cada tipo de problema para graficarlos
            for i, problema in enumerate(problemas_unicos):
                problema_df = estacion_df[estacion_df["tipo_problema"] == problema]

                # Contar la cantidad de problemas por día
                problemas_por_dia = problema_df.groupby("dia_reclamo").size()

                # Asegurar que los días faltantes tengan valor 0 (hasta 31 días)
                problemas_por_dia = problemas_por_dia.reindex(range(1, 32), fill_value=0)

                # Graficar la línea
                ax.plot(
                    problemas_por_dia.index,
                    problemas_por_dia.values,
                    label=f"{problema}",  # Nombre del problema
                    color=colores_lineas[i]
                )

        # Configuración del gráfico (dentro del bucle por estación)
            ax.set_title(f"Línea de Tiempo de Incidencias - {estacion}", fontsize=16)
            ax.set_xlabel("Día del Mes", fontsize=12)
            ax.set_ylabel("Cantidad de incidencias", fontsize=12)
            ax.set_xticks(range(1, 32))
            ax.set_xticklabels(range(1, 32), rotation=45)

            # Añadir una leyenda
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)

            # Ajustar el diseño
            plt.tight_layout()

            # Convertir el gráfico a base64 y guardarlo en HTML
            with BytesIO() as buffer:
                plt.savefig(buffer, format="png")
                buffer.seek(0)
                plot_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            plt.close()

            # Añadir el gráfico al HTML
            linea_dia_html += f"""
            <h2>Estación: {estacion}</h2>
            <img src="data:image/png;base64,{plot_base64}" alt="Gráfico de Problemas - {estacion}">
            """
        html_content += linea_dia_html
        
    # Finalizar HTML
    html_content += "</body></html>"
    

    return HTMLResponse(content=html_content)
