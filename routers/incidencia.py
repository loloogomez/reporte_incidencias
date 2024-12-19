from fastapi import APIRouter, HTTPException, Depends, Query
from db import schemas, models
from db.client import SessionLocal
from sqlalchemy.orm import Session, aliased
from datetime import datetime, time
from routers.auth import get_current_user
from typing import Optional
from math import ceil

router = APIRouter(prefix="/incidencia", tags=["incidencia"], responses={404: {"message": "No encontrado"}}, dependencies=[Depends(get_current_user)])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Obtener todas las incidencias
@router.get("/", response_model=list[schemas.Incidencia], status_code=200)
async def get_incidencias(db: Session = Depends(get_db)):
    return db.query(models.Incidencia).all()

# Obtener incidencias por línea
@router.get("/detalladas", response_model=dict, status_code=200)
async def get_incidencias_por_linea(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    lineaID: Optional[int] = None,
    finalizada: Optional[bool] = None,
    page: int = Query(1, ge=1, description="Número de la página"),
    per_page: int = Query(20, ge=1, le=100, description="Resultados por página"),
    db: Session = Depends(get_db),
):
    
    # Alias para los usuarios
    UsuarioCliente = aliased(models.Usuario)
    UsuarioTecnico = aliased(models.Usuario)
    
    query = (
        db.query(
            models.Incidencia,
            UsuarioCliente.nombre_usuario.label('nombre_cliente'),
            UsuarioTecnico.nombre_usuario.label('nombre_tecnico'),
            models.Equipamiento.numero_chasis.label('chasis'),
            models.Equipamiento.tipo_equipamiento.label('tipo_equipamiento'),
            models.Estacion.nombre_estacion.label('nombre_estacion'),
            models.Linea.nombre_linea.label('nombre_linea')
        )
        .join(models.Equipamiento, models.Incidencia.id_equipamiento == models.Equipamiento.id_equipamiento)
        .join(models.Estacion, models.Equipamiento.id_estacion_asociada == models.Estacion.id_estacion)
        .join(models.Linea, models.Estacion.id_linea_asociada == models.Linea.id_linea)
        .outerjoin(UsuarioCliente, models.Incidencia.id_cliente == UsuarioCliente.id_usuario)
        .outerjoin(UsuarioTecnico, models.Incidencia.id_tecnico_asignado == UsuarioTecnico.id_usuario)
    )
    
    # Filtros
    if fecha_desde:
        fecha_desde = datetime.strptime(fecha_desde, "%Y-%m-%d")  # Convertir a objeto datetime
        query = query.filter(models.Incidencia.fecha_reclamo >= fecha_desde)
        
    if fecha_hasta:
        fecha_hasta = datetime.strptime(fecha_hasta, "%Y-%m-%d")  # Convertir a objeto datetime
        
        # Asegurarnos de que 'fecha_hasta' incluya todo el día (23:59:59)
        if fecha_hasta.time() == time(0, 0):  # Si la hora es 00:00:00, setear al final del día
            fecha_hasta = fecha_hasta.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        query = query.filter(models.Incidencia.fecha_reclamo <= fecha_hasta)
    
    if lineaID:
        query = query.filter(models.Linea.id_linea == lineaID)
    
    if finalizada:
        query = query.filter(models.Incidencia.flag == "Finalizada")
    else:
        query = query.filter(models.Incidencia.flag != "Finalizada")

    query = query.order_by(models.Incidencia.fecha_reclamo.desc())
    
    # Contar el total de resultados
    total_results = query.count()
        
    # Calcular paginación
    total_pages = ceil(total_results / per_page)
    offset = (page - 1) * per_page

    # Aplicar paginación
    results = query.offset(offset).limit(per_page).all()
    
    response = []
     
    for incidencia, nombre_cliente, nombre_tecnico, chasis, tipo_equipamiento, nombre_estacion, nombre_linea in results:
        response.append(schemas.IncidenciaCompleta(
            id_incidencia=incidencia.id_incidencia,
            fecha_reclamo=incidencia.fecha_reclamo,
            fecha_finalizacion=incidencia.fecha_finalizacion,
            prioridad=incidencia.prioridad,
            flag=incidencia.flag,
            tipo_problema=incidencia.tipo_problema,
            descripcion=incidencia.descripcion,
            tipo_resolucion=incidencia.tipo_resolucion,
            nombre_cliente=nombre_cliente,
            nombre_tecnico=nombre_tecnico,
            chasis=chasis,
            tipo_equipamiento=tipo_equipamiento,
            nombre_estacion=nombre_estacion,
            nombre_linea=nombre_linea  
        ))
    
    return {
        "incidencias": response,
        "page": page,
        "per_page": per_page,
        "total": total_results,
        "pages": total_pages
    }

# Obtener incidencia por ID
@router.get("/get_incidencia/{id_incidencia}", response_model=schemas.Incidencia, status_code=200)
async def get_incidencia(id_incidencia: int, db: Session = Depends(get_db)):
    incidencia = db.query(models.Incidencia).filter(models.Incidencia.id_incidencia == id_incidencia).first()
    if not incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    return incidencia

# Obtener incidencias por línea
@router.get("/linea_asociada", response_model=dict, status_code=200)
async def get_incidencias_por_linea(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    finalizada: Optional[bool] = None,
    page: int = Query(1, ge=1, description="Número de la página"),
    per_page: int = Query(20, ge=1, le=100, description="Resultados por página"),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    
    id_linea = current_user.id_linea_asociada
    
    # Alias para los usuarios
    UsuarioCliente = aliased(models.Usuario)
    UsuarioTecnico = aliased(models.Usuario)
    
    query = (
        db.query(
            models.Incidencia,
            UsuarioCliente.nombre_usuario.label('nombre_cliente'),
            UsuarioTecnico.nombre_usuario.label('nombre_tecnico'),
            models.Equipamiento.numero_chasis.label('chasis'),
            models.Equipamiento.tipo_equipamiento.label('tipo_equipamiento'),
            models.Estacion.nombre_estacion.label('nombre_estacion'),
            models.Linea.nombre_linea.label('nombre_linea')
        )
        .join(models.Equipamiento, models.Incidencia.id_equipamiento == models.Equipamiento.id_equipamiento)
        .join(models.Estacion, models.Equipamiento.id_estacion_asociada == models.Estacion.id_estacion)
        .join(models.Linea, models.Estacion.id_linea_asociada == models.Linea.id_linea)
        .outerjoin(UsuarioCliente, models.Incidencia.id_cliente == UsuarioCliente.id_usuario)
        .outerjoin(UsuarioTecnico, models.Incidencia.id_tecnico_asignado == UsuarioTecnico.id_usuario)
        .filter(models.Estacion.id_linea_asociada == id_linea)
    )
    
    # Aplicar filtro por fecha si se proporciona
    if fecha_desde:
        fecha_desde = datetime.strptime(fecha_desde, "%Y-%m-%d")  # Convertir a objeto datetime
        query = query.filter(models.Incidencia.fecha_reclamo >= fecha_desde)
        
    if fecha_hasta:
        fecha_hasta = datetime.strptime(fecha_hasta, "%Y-%m-%d")  # Convertir a objeto datetime
        
        # Asegurarnos de que 'fecha_hasta' incluya todo el día (23:59:59)
        if fecha_hasta.time() == time(0, 0):  # Si la hora es 00:00:00, setear al final del día
            fecha_hasta = fecha_hasta.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        query = query.filter(models.Incidencia.fecha_reclamo <= fecha_hasta)
        
    if finalizada:
        query = query.filter(models.Incidencia.flag == "Finalizada")
    else:
        query = query.filter(models.Incidencia.flag != "Finalizada")

    # Ejecutar la consulta
    query = query.order_by(models.Incidencia.fecha_reclamo.desc())
    
    # Contar el total de resultados
    total_results = query.count()
        
    # Calcular paginación
    total_pages = ceil(total_results / per_page)
    offset = (page - 1) * per_page

    # Aplicar paginación
    incidencias = query.offset(offset).limit(per_page).all()
    
    response = []
     
    for incidencia, nombre_cliente, nombre_tecnico, chasis, tipo_equipamiento, nombre_estacion, nombre_linea in incidencias:
        response.append(schemas.IncidenciaCompleta(
            id_incidencia=incidencia.id_incidencia,
            fecha_reclamo=incidencia.fecha_reclamo,
            fecha_finalizacion=incidencia.fecha_finalizacion,
            prioridad=incidencia.prioridad,
            flag=incidencia.flag,
            tipo_problema=incidencia.tipo_problema,
            descripcion=incidencia.descripcion,
            tipo_resolucion=incidencia.tipo_resolucion,
            nombre_cliente=nombre_cliente,
            nombre_tecnico=nombre_tecnico,
            chasis=chasis,
            tipo_equipamiento=tipo_equipamiento,
            nombre_estacion=nombre_estacion,
            nombre_linea=nombre_linea  
        ))
    
    return {
        "incidencias": response,
        "page": page,
        "per_page": per_page,
        "total": total_results,
        "pages": total_pages
    }

# Obtener Incidencias Pendientes o pausadas de un equipamiento
@router.get("/abiertas/{id_equipamiento_seleccionado}", status_code=200)
async def incidencias_abiertas(id_equipamiento_seleccionado: int, db: Session = Depends(get_db)):
    
    db_equipamiento = db.query(models.Equipamiento).filter(models.Equipamiento.id_equipamiento == id_equipamiento_seleccionado).first()
    if not db_equipamiento:
        raise HTTPException(status_code=404, detail="Equipamiento no encontrado")
    
    # Verificar si tiene incidencias abiertas (Pendiente o Pausada)
    incidencias_abiertas = (
        db.query(models.Incidencia)
        .filter(models.Incidencia.id_equipamiento == id_equipamiento_seleccionado)
        .filter(models.Incidencia.flag.in_(["Pendiente", "Pausada"]))
        .count()
    )
    
    # Retornar true si tiene incidencias abiertas, false si no
    return {"incidencias_abiertas": incidencias_abiertas > 0}


# Crear nueva incidencia
@router.post("/", response_model=schemas.Incidencia, status_code=201)
async def create_incidencia(incidencia: schemas.IncidenciaCreate, db: Session = Depends(get_db)):

    if incidencia.id_tecnico_asignado:
        db_tecnico = db.query(models.Usuario).filter(models.Usuario.id_usuario == incidencia.id_tecnico_asignado).first()
        if not db_tecnico:
            raise HTTPException(status_code=404, detail="Técnico no encontrado")

    db_cliente = db.query(models.Usuario).filter(models.Usuario.id_usuario == incidencia.id_cliente).first()
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    db_equipamiento = db.query(models.Equipamiento).filter(models.Equipamiento.id_equipamiento == incidencia.id_equipamiento).first()
    if not db_equipamiento:
        raise HTTPException(status_code=404, detail="Equipamiento no encontrado")
    
    incidencia.fecha_reclamo = datetime.now()

    new_incidencia = models.Incidencia(**incidencia.dict())
    db.add(new_incidencia)
    db.commit()
    db.refresh(new_incidencia)
    return new_incidencia

# Actualizar incidencia por ID
@router.put("/{id_incidencia}", response_model=schemas.Incidencia, status_code=200)
async def update_incidencia(id_incidencia: int, incidencia: schemas.IncidenciaUpdate, db: Session = Depends(get_db)):
    db_incidencia = db.query(models.Incidencia).filter(models.Incidencia.id_incidencia == id_incidencia).first()
    if not db_incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    if incidencia.id_tecnico_asignado:
        db_tecnico = db.query(models.Usuario).filter(models.Usuario.id_usuario == incidencia.id_tecnico_asignado).filter(models.Usuario.role != "cliente").first()
        if not db_tecnico:
            raise HTTPException(status_code=404, detail="Técnico no encontrado")

    db_cliente = db.query(models.Usuario).filter(models.Usuario.id_usuario == incidencia.id_cliente).first()
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    db_equipamiento = db.query(models.Equipamiento).filter(models.Equipamiento.id_equipamiento == incidencia.id_equipamiento).first()
    if not db_equipamiento:
        raise HTTPException(status_code=404, detail="Equipamiento no encontrado")
    
    for key, value in incidencia.dict(exclude_unset=True).items():
        setattr(db_incidencia, key, value)
    db.commit()
    db.refresh(db_incidencia)
    return db_incidencia

# Eliminar incidencia por ID
@router.delete("/{id_incidencia}", status_code=204)
async def delete_incidencia(id_incidencia: int, db: Session = Depends(get_db)):
    db_incidencia = db.query(models.Incidencia).filter(models.Incidencia.id_incidencia == id_incidencia).first()
    if not db_incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    db.delete(db_incidencia)
    db.commit()
    return {"message": "Incidencia eliminada"}

@router.put("/{id_incidencia}/finalizar", response_model=schemas.Incidencia, status_code=200)
async def finalizar_incidencia(
    id_incidencia: int,
    tipo_finalizacion: Optional[schemas.TipoResolucion] = None,
    db: Session = Depends(get_db),
    current_user: schemas.Usuario = Depends(get_current_user)
):
    # Buscar la incidencia en la base de datos
    db_incidencia = db.query(models.Incidencia).filter(models.Incidencia.id_incidencia == id_incidencia).first()
    if not db_incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    
    # Actualizar la fecha de finalización
    db_incidencia.fecha_finalizacion = datetime.now()
    
    # Actualizar el estado de la incidencia
    db_incidencia.flag = "Finalizada"
    
    # Asignar el técnico que cierra la incidencia
    db_incidencia.id_tecnico_asignado = current_user.id_usuario
    
    # Si se proporciona un tipo de finalización, actualizarlo
    if tipo_finalizacion.tipo_resolucion:
        db_incidencia.tipo_resolucion = tipo_finalizacion.tipo_resolucion
        
    # Guardar cambios en la base de datos
    db.commit()
    db.refresh(db_incidencia)
    
    return db_incidencia