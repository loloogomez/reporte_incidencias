from datetime import datetime
from fastapi.responses import HTMLResponse
from fastapi import APIRouter, HTTPException, Depends, Query
from db import models
from db.client import SessionLocal
from sqlalchemy.orm import Session
from routers.auth import get_current_user

import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import numpy as np


router = APIRouter(prefix="/estadistica", tags=["estadistica"], responses={404: {"message": "No encontrado"}}, dependencies=[Depends(get_current_user)])

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
            models.Equipamiento.tipo_equipamiento,
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
    columnas = ["tipo_problema", "nombre_linea", "nombre_estacion", "fecha_reclamo", "fecha_finalizacion", "prioridad", "tipo_equipamiento"]
    datos_df = pd.DataFrame(incidencias, columns=columnas)
    
    datos_df["tiempo_resolucion"] = (datos_df["fecha_finalizacion"] - datos_df["fecha_reclamo"]).dt.days
    
    # Resumir los datos por estación y tipo de problema
    resumen_lineas = datos_df.groupby(["nombre_linea", "tipo_problema"]).size().unstack(fill_value=1)


    # Contenedor para HTML de gráficos
    html_content = "<html><head><title>Gráficos Solicitados</title></head><body>"
    
    if "top_estaciones" in graficos_solicitados:
        # Agrupar datos por estación y línea, contar incidencias
        top_estaciones = (
            datos_df.groupby(["nombre_estacion", "nombre_linea"])
            .size()
            .reset_index(name="Cantidad")
            .sort_values(by="Cantidad", ascending=False)
            .head(10)  # Tomar las 10 estaciones con más incidencias
        )

        # Crear etiquetas combinadas de estación y línea
        top_estaciones["Etiqueta"] = top_estaciones["nombre_estacion"] + "\n" + top_estaciones["nombre_linea"]

        # Configurar el gráfico
        plt.figure(figsize=(12, 8))
        ax = sns.barplot(
            x="Cantidad", 
            y="Etiqueta", 
            data=top_estaciones, 
            hue="Etiqueta",  # Asignar el eje `y` como `hue`
            palette="coolwarm", 
            edgecolor="black", 
            dodge=False,  # Evitar desplazamiento entre barras
            legend=False  # Ocultar la leyenda
        )
        plt.title("Top 10 Estaciones con Más Incidencias Reportadas", fontsize=16)
        plt.xlabel("Cantidad de Incidencias", fontsize=12)
        plt.ylabel("Estación - Línea", fontsize=12)
        plt.xticks(fontsize=10)
        plt.yticks(fontsize=10)
        
        # Añadir etiquetas con la cantidad de incidencias en cada barra
        for container in ax.containers:
            ax.bar_label(container, fmt="%d", fontsize=10, padding=3)

        # Guardar gráfico como imagen base64
        with BytesIO() as buffer:
            plt.savefig(buffer, format="png")
            buffer.seek(0)
            top_estaciones_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        plt.close()

        # Añadir el gráfico al HTML
        html_content += f"""
        <div style="text-align: center;">
            <img src="data:image/png;base64,{top_estaciones_base64}" alt="Gráfico de barras - Top 10 Estaciones">
        </div>
        """
    
    # Bubble Chart
    """
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
    """
        
    
    # Gráfico de barras con diferenciación por rango
    """
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
    
    """
        
        
    # Barras por tipo de incidencia
    if "tipo_incidencia_barra" in graficos_solicitados:
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
        
    # Gráfico de torta total lineas
    if "torta_general" in graficos_solicitados:
    # Resumir datos para el gráfico de torta
        resumen_lineas = datos_df.groupby("nombre_linea").size().reset_index(name="Cantidad")
        total_incidencias = resumen_lineas["Cantidad"].sum()  # Total de incidencias reportadas
        colores = sns.color_palette("pastel")[:len(resumen_lineas["Cantidad"])]

        # Crear la figura del gráfico
        plt.figure(figsize=(10, 8))
        plt.pie(
            resumen_lineas["Cantidad"], 
            labels=resumen_lineas["nombre_linea"], 
            autopct=lambda p: f'{int(round(p * total_incidencias / 100))}',  # Cantidad absoluta
            startangle=140,
            colors=colores,
            wedgeprops={"linewidth": 1.5, "edgecolor": "white"}, frame=False
        )
        plt.title(f"Distribución de Incidencias por Línea\nTotal: {total_incidencias} incidencias", fontsize=16)
        plt.axis('equal')

        # Guardar gráfico como imagen base64
        with BytesIO() as buffer:
            plt.savefig(buffer, format="png")
            buffer.seek(0)
            torta_total_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        plt.close()

        # Añadir el gráfico al HTML
        html_content += f"""
        <div style="text-align: center;">
            <img src="data:image/png;base64,{torta_total_base64}" alt="Gráfico de torta de incidencias general">
        </div>
        """
    
        
    # Gráfico de torta tipo problema por linea
    if "torta_por_linea" in graficos_solicitados:
        pie_html_lineas = '<div style="display: flex; flex-wrap: wrap; gap: 100%;">'

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
            pie_html_lineas += f'<div style="width: 100%;"><h3>Línea: {linea}</h3><img src="data:image/png;base64,{linea_base64}"></div>'

        pie_html_lineas += '</div>'
        html_content += pie_html_lineas
        
    # Volumen mensual por linea
    """
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
            linea_mes_html += f
            <h2>Estación: {estacion}</h2>
            <img src="data:image/png;base64,{plot_base64}" alt="Gráfico de Problemas - {estacion}">
            
        html_content += linea_mes_html
    """    
    
    # GRAFICO DIARIO
    if "volumen_diario_por_linea" in graficos_solicitados:
        linea_dia_html = ""
        lineas_unicas = datos_df["nombre_linea"].unique()
        problemas_unicos = datos_df["tipo_problema"].unique()

        # Convertir la columna de fecha a formato datetime y extraer el día
        datos_df["fecha_reclamo"] = pd.to_datetime(datos_df["fecha_reclamo"])
        datos_df["dia_reclamo"] = datos_df["fecha_reclamo"].dt.day

        for linea in lineas_unicas:
            linea_df = datos_df[datos_df["nombre_linea"] == linea]
            colores_lineas = sns.color_palette("pastel")[:len(problemas_unicos)]

            # Crear una nueva figura para cada estación
            fig, ax = plt.subplots(figsize=(12, 8))

            # Iterar sobre cada tipo de problema para graficarlos
            for i, problema in enumerate(problemas_unicos):
                problema_df = linea_df[linea_df["tipo_problema"] == problema]

                # Contar la cantidad de problemas por día
                problemas_por_dia = problema_df.groupby("dia_reclamo").size()

                # Asegurar que los días faltantes tengan valor 0 (hasta 31 días)
                problemas_por_dia = problemas_por_dia.reindex(range(1, 32), fill_value=0)

                # Graficar la línea
                ax.plot(
                    problemas_por_dia.index,
                    problemas_por_dia.values,
                    label=f"{problema}",  # Nombre del problema
                    color=colores_lineas[i],
                    linewidth=4
                )

        # Configuración del gráfico (dentro del bucle por estación)
            ax.set_title(f"Línea de Tiempo de Incidencias - {linea}", fontsize=16)
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
            <h2>Línea: {linea}</h2>
            <img src="data:image/png;base64,{plot_base64}" alt="Gráfico de incidencias - {linea}">
            """
        html_content += linea_dia_html
        
        # Gráfico de torta por tipo de equipamiento
    if "equipamiento_pie" in graficos_solicitados:
        resumen_equipamiento = datos_df.groupby("tipo_equipamiento").size().reset_index(name="Cantidad")
        total_equipos = resumen_equipamiento["Cantidad"].sum()
        colores = sns.color_palette("pastel", len(resumen_equipamiento))

        plt.figure(figsize=(10, 8))
        plt.pie(
            resumen_equipamiento["Cantidad"], 
            labels=resumen_equipamiento["tipo_equipamiento"],
            autopct=lambda p: f'{p:.1f}%',
            startangle=140,
            colors=colores,
            wedgeprops={"linewidth": 1.5, "edgecolor": "white"}
        )
        plt.title(f"Distribución de Incidencias por Tipo de Equipamiento\nTotal: {total_equipos} incidencias", fontsize=16)
        plt.axis('equal')

        with BytesIO() as buffer:
            plt.savefig(buffer, format="png")
            buffer.seek(0)
            equip_pie_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        plt.close()

        html_content += f"""
        <div style="text-align: center;">
            <h3>Distribución por Tipo de Equipamiento</h3>
            <img src="data:image/png;base64,{equip_pie_base64}" alt="Torta equipamiento">
        </div>
        """

    # Gráfico de barras por tipo de equipamiento
    if "equipamiento_barra" in graficos_solicitados:
        resumen_equipamiento = datos_df.groupby("tipo_equipamiento").size().reset_index(name="Cantidad")

        plt.figure(figsize=(12, 8))
        ax = sns.barplot(
            x="tipo_equipamiento", 
            y="Cantidad", 
            data=resumen_equipamiento,
            palette="viridis",
            edgecolor="black"
        )
        plt.title("Cantidad de Incidencias por Tipo de Equipamiento", fontsize=16)
        plt.xlabel("Tipo de Equipamiento", fontsize=12)
        plt.ylabel("Cantidad de Incidencias", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        
        # Añadir etiquetas
        for container in ax.containers:
            ax.bar_label(container, fmt="%d", fontsize=10, padding=3)

        with BytesIO() as buffer:
            plt.savefig(buffer, format="png", bbox_inches="tight")
            buffer.seek(0)
            equip_barra_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        plt.close()

        html_content += f"""
        <div style="text-align: center;">
            <h3>Incidencias por Tipo de Equipamiento</h3>
            <img src="data:image/png;base64,{equip_barra_base64}" alt="Barras equipamiento">
        </div>
        """

    # Gráfico de vandalismo por línea (modificado a treemap)
    if "vandalismo_lineas" in graficos_solicitados:
        vandalismo_df = datos_df[datos_df["tipo_problema"] == "Vandalismo"]
        
        if not vandalismo_df.empty:
            resumen_vandalismo = vandalismo_df.groupby("nombre_linea").size().reset_index(name="Cantidad")
            
            # Importar squarify (asegúrate de tenerlo instalado: pip install squarify)
            import squarify

            plt.figure(figsize=(12, 8))
            sizes = resumen_vandalismo["Cantidad"]
            # Crear etiquetas que muestren la línea y la cantidad de incidencias
            labels = [f"{row['nombre_linea']}\n{row['Cantidad']}" for _, row in resumen_vandalismo.iterrows()]
            
            # Generar el treemap; se utiliza un cmap para los colores según la cantidad
            cmap = plt.cm.Reds
            # Normalizar los tamaños para asignar colores
            colores = [cmap(float(val) / max(sizes)) for val in sizes]
            # Dibujar el treemap
            squarify.plot(sizes=sizes, label=labels, color=colores, alpha=0.8, pad=True)
            
            plt.axis('off')
            plt.title("Incidencias de Vandalismo por Línea", fontsize=16)
            
            # Guardar el gráfico como imagen base64
            with BytesIO() as buffer:
                plt.savefig(buffer, format="png", bbox_inches="tight")
                buffer.seek(0)
                vandalismo_treemap_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            plt.close()
            
            html_content += f"""
            <div style="text-align: center;">
                <h3>Incidencias de Vandalismo por Línea</h3>
                <img src="data:image/png;base64,{vandalismo_treemap_base64}" alt="Treemap de vandalismo por línea">
            </div>
            """
        else:
            html_content += "<p>No se encontraron incidencias de vandalismo en el período seleccionado.</p>"
        
    # Finalizar HTML
    html_content += "</body></html>"
    

    return HTMLResponse(content=html_content)
