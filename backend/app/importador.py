"""Importa automáticamente los FUR (frenos, suspensión, alineación, ruidos) que la
aplicación emisora deja como archivos JSON en `settings.buffer_dir`.

IMPORTANTE: `buffer_dir` es de la app emisora, no nuestro. Este módulo SOLO LEE
esa carpeta — nunca mueve, renombra ni borra nada ahí dentro. Para no
reimportar un archivo en cada revisión (cada `buffer_intervalo_seg`), se lleva
un registro de nombres ya vistos en la tabla `archivos_importados`.
"""

import json
import logging
from pathlib import Path

from sqlalchemy import select

from . import parsing, storage
from .config import settings
from .db import SessionLocal
from .models import ArchivoImportado, Prueba

logger = logging.getLogger(__name__)

# Cuántos archivos se preparan por transacción. Con un lote grande, un backlog
# de miles de archivos hace un puñado de commits en vez de uno por archivo.
LOTE = 200


def _buffer_dir() -> Path:
    d = Path(settings.buffer_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


def migrar_carpetas_antiguas() -> None:
    """Deshace, una sola vez, el movimiento a `procesados/`/`errores/` de una
    versión anterior de este importador (ver incidente: eso rompió el uso que
    la app principal le da a `buffer_dir`). Si esas carpetas no existen, no
    hace nada. Es seguro llamarla en cada arranque."""
    buf = _buffer_dir()
    for carpeta, estado in (("procesados", "ok"), ("errores", "error")):
        sub = buf / carpeta
        if not sub.is_dir():
            continue

        archivos = sorted(sub.glob("*.json"))
        if archivos:
            logger.warning(
                "Migrando %d archivo(s) de %s de vuelta a %s (no se vuelve a mover nada)",
                len(archivos), sub, buf,
            )
        db = SessionLocal()
        try:
            existentes = {
                n for (n,) in db.execute(select(ArchivoImportado.nombre_archivo))
            }
            for ruta in archivos:
                if ruta.name not in existentes:
                    db.add(ArchivoImportado(
                        nombre_archivo=ruta.name, estado=estado,
                        detalle="migrado desde carpeta antigua",
                    ))
                ruta.rename(buf / ruta.name)
            db.commit()
        finally:
            db.close()

        try:
            sub.rmdir()
        except OSError:
            pass  # no estaba vacía (archivo no-.json, etc.) — se deja como está


def _preparar_prueba(ruta: Path) -> Prueba:
    """Lee el JSON (sin tocar el archivo original) y arma el registro."""
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


def _importar_lote(rutas: list[Path]) -> tuple[int, int]:
    """Procesa un lote en una sola transacción. No toca los archivos originales.
    Devuelve (importados, con_error)."""
    importados = con_error = 0
    db = SessionLocal()
    try:
        for ruta in rutas:
            try:
                prueba = _preparar_prueba(ruta)
            except Exception as e:
                logger.exception("No se pudo importar %s", ruta.name)
                db.add(ArchivoImportado(
                    nombre_archivo=ruta.name, estado="error", detalle=str(e)[:500],
                ))
                con_error += 1
                continue
            db.add(prueba)
            db.add(ArchivoImportado(nombre_archivo=ruta.name, estado="ok"))
            importados += 1
        db.commit()
    except Exception:
        logger.exception("Fallo de base de datos importando un lote de %d archivos", len(rutas))
        db.rollback()
        return 0, 0
    finally:
        db.close()
    return importados, con_error


def escanear_buffer() -> dict:
    """Revisa `buffer_dir` (solo su raíz, sin tocar nada) e importa los .json
    que no estén ya en `archivos_importados`."""
    resumen = {"importados": 0, "errores": 0}

    archivos = sorted(_buffer_dir().glob("*.json"))
    if not archivos:
        return resumen

    db = SessionLocal()
    try:
        vistos = {n for (n,) in db.execute(select(ArchivoImportado.nombre_archivo))}
    finally:
        db.close()

    pendientes = [r for r in archivos if r.name not in vistos]
    if not pendientes:
        return resumen

    total = len(pendientes)
    logger.info("Importando %d archivo(s) nuevo(s) de %s", total, _buffer_dir())

    for inicio in range(0, total, LOTE):
        lote = pendientes[inicio : inicio + LOTE]
        importados, con_error = _importar_lote(lote)
        resumen["importados"] += importados
        resumen["errores"] += con_error
        logger.info(
            "Importación: %d/%d revisados (%d ok, %d con error)",
            min(inicio + LOTE, total), total, resumen["importados"], resumen["errores"],
        )

    return resumen
