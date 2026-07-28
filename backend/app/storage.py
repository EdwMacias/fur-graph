import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .config import settings

_SLUG = re.compile(r"[^A-Za-z0-9_-]")


def _data_dir() -> Path:
    d = Path(settings.data_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


def guardar_json(id_prueba: int | None, tipo: str, contenido: bytes) -> tuple[str, str]:
    """Guarda el JSON crudo y devuelve (nombre_archivo, ruta_absoluta)."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    base = f"{id_prueba if id_prueba is not None else 'NA'}_{tipo}_{ts}"
    nombre = _SLUG.sub("_", base) + ".json"
    ruta = _data_dir() / nombre
    ruta.write_bytes(contenido)
    return nombre, str(ruta)


def leer_json(ruta: str) -> dict:
    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data[0] if isinstance(data, list) and data else data
