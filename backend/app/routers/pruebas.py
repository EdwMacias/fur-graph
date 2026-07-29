import json

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import auth, importador, parsing, storage
from ..config import settings
from ..db import get_db
from ..models import Prueba
from ..schemas import IngestaOut, PruebaOut

router = APIRouter(prefix="/api/pruebas", tags=["pruebas"])


def _verificar_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="API key inválida o ausente")


def _verificar_sesion(request: Request) -> None:
    if not auth.token_valido(request.cookies.get(auth.COOKIE_NAME)):
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")


@router.post("", response_model=IngestaOut, dependencies=[Depends(_verificar_api_key)])
async def ingestar(
    request: Request,
    file: UploadFile | None = None,
    db: Session = Depends(get_db),
):
    """Recibe un FUR como archivo (multipart 'file') o como JSON crudo en el body."""
    if file is not None:
        contenido = await file.read()
    else:
        contenido = await request.body()

    if not contenido:
        raise HTTPException(status_code=400, detail="Cuerpo vacío")

    try:
        data = json.loads(contenido)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="JSON inválido")

    obj = data[0] if isinstance(data, list) and data else data
    try:
        tipo, esquema = parsing.detectar(obj)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    id_prueba = obj.get("IdPrueba")
    nombre, ruta = storage.guardar_json(id_prueba, tipo, contenido)

    prueba = Prueba(
        id_prueba=id_prueba,
        tipo=tipo,
        esquema=esquema,
        nombre_archivo=nombre,
        ruta_archivo=ruta,
        fecha_prueba=parsing.parsear_fecha(obj.get("Fecha")),
        bytes=len(contenido),
    )
    db.add(prueba)
    db.commit()
    db.refresh(prueba)
    return IngestaOut(id=prueba.id, tipo=tipo, esquema=esquema)


@router.post("/importar", dependencies=[Depends(_verificar_api_key)])
def importar():
    """Fuerza una revisión inmediata de `buffer_dir` (normalmente corre sola cada
    `buffer_intervalo_seg`)."""
    return importador.escanear_buffer()


@router.get("", response_model=list[PruebaOut], dependencies=[Depends(_verificar_sesion)])
def listar(
    tipo: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Prueba).order_by(Prueba.recibido_en.desc())
    if tipo:
        stmt = stmt.where(Prueba.tipo == tipo.upper())
    stmt = stmt.limit(limit).offset(offset)
    return db.scalars(stmt).all()


@router.get("/{prueba_id}", response_model=PruebaOut, dependencies=[Depends(_verificar_sesion)])
def obtener(prueba_id: int, db: Session = Depends(get_db)):
    prueba = db.get(Prueba, prueba_id)
    if not prueba:
        raise HTTPException(status_code=404, detail="Prueba no encontrada")
    return prueba


@router.get("/{prueba_id}/datos", dependencies=[Depends(_verificar_sesion)])
def datos(prueba_id: int, db: Session = Depends(get_db)):
    """Devuelve los paneles/series/métricas listos para graficar (con downsampling)."""
    prueba = db.get(Prueba, prueba_id)
    if not prueba:
        raise HTTPException(status_code=404, detail="Prueba no encontrada")
    try:
        raw = storage.leer_json(prueba.ruta_archivo)
    except FileNotFoundError:
        raise HTTPException(status_code=410, detail="Archivo de datos no disponible")
    return parsing.normalizar(raw)


@router.get("/{prueba_id}/raw", dependencies=[Depends(_verificar_sesion)])
def raw(prueba_id: int, db: Session = Depends(get_db)):
    prueba = db.get(Prueba, prueba_id)
    if not prueba:
        raise HTTPException(status_code=404, detail="Prueba no encontrada")
    return FileResponse(
        prueba.ruta_archivo, media_type="application/json", filename=prueba.nombre_archivo
    )
