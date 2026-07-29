"""Importa automáticamente los FUR (frenos, suspensión, alineación, ruidos) que la
aplicación emisora deja como archivos JSON en `settings.buffer_dir`.

Un bucle en segundo plano (ver `main.lifespan`) llama a `escanear_buffer` cada
`buffer_intervalo_seg`. Cada archivo se mueve a `procesados/` si se importa
correctamente, o a `errores/` si falla, para no reprocesarlo en la siguiente
pasada.
"""

import json
import logging
from pathlib import Path

from . import parsing, storage
from .config import settings
from .db import SessionLocal
from .models import Prueba

logger = logging.getLogger(__name__)


def _buffer_dir() -> Path:
    d = Path(settings.buffer_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _subdir(nombre: str) -> Path:
    d = _buffer_dir() / nombre
    d.mkdir(parents=True, exist_ok=True)
    return d


# Cuántos archivos se preparan por transacción. Con un lote grande, un backlog
# de miles de archivos hace un puñado de commits en vez de uno por archivo.
LOTE = 200


def _preparar_prueba(ruta: Path) -> Prueba:
    """Lee y guarda el JSON crudo, y arma el registro (sin insertarlo aún)."""
    contenido = ruta.read_bytes()
    data = json.loads(contenido)
    obj = data[0] if isinstance(data, list) and data else data

    tipo, esquema = parsing.detectar(obj)
    id_prueba = obj.get("IdPrueba")
    nombre, ruta_guardada = storage.guardar_json(id_prueba, tipo, contenido)

    return Prueba(
        id_prueba=id_prueba,
        tipo=tipo,
        esquema=esquema,
        nombre_archivo=nombre,
        ruta_archivo=ruta_guardada,
        fecha_prueba=parsing.parsear_fecha(obj.get("Fecha")),
        bytes=len(contenido),
    )


def _importar_lote(rutas: list[Path]) -> tuple[list[Path], list[Path]]:
    """Prepara e inserta un lote en una sola transacción. Devuelve (ok, con_error)."""
    ok, con_error = [], []
    db = SessionLocal()
    try:
        for ruta in rutas:
            try:
                prueba = _preparar_prueba(ruta)
            except Exception:
                logger.exception("No se pudo importar %s", ruta.name)
                con_error.append(ruta)
                continue
            db.add(prueba)
            ok.append(ruta)
        db.commit()
    except Exception:
        logger.exception("Fallo de base de datos importando un lote de %d archivos", len(rutas))
        db.rollback()
        con_error.extend(ok)
        ok = []
    finally:
        db.close()
    return ok, con_error


def escanear_buffer() -> dict:
    """Revisa `buffer_dir` en busca de archivos .json nuevos y los importa por lotes."""
    resumen = {"importados": 0, "errores": 0}
    procesados = _subdir("procesados")
    errores = _subdir("errores")

    archivos = sorted(_buffer_dir().glob("*.json"))
    if not archivos:
        return resumen

    total = len(archivos)
    logger.info("Importando %d archivo(s) de %s", total, _buffer_dir())

    for inicio in range(0, total, LOTE):
        lote = archivos[inicio : inicio + LOTE]
        ok, con_error = _importar_lote(lote)

        for ruta in ok:
            ruta.rename(procesados / ruta.name)
        for ruta in con_error:
            ruta.rename(errores / ruta.name)

        resumen["importados"] += len(ok)
        resumen["errores"] += len(con_error)
        logger.info(
            "Importación: %d/%d procesados (%d ok, %d con error)",
            min(inicio + LOTE, total), total, resumen["importados"], resumen["errores"],
        )

    return resumen
