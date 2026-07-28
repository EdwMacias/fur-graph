from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PruebaOut(BaseModel):
    """Metadatos de una prueba para el listado y el detalle."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    id_prueba: int | None
    tipo: str
    esquema: str
    nombre_archivo: str
    fecha_prueba: datetime | None
    recibido_en: datetime
    bytes: int


class IngestaOut(BaseModel):
    id: int
    tipo: str
    esquema: str
