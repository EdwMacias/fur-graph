from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


class Prueba(Base):
    """Metadatos de una prueba FUR. El JSON crudo vive en disco (ruta_archivo)."""

    __tablename__ = "pruebas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_prueba: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tipo: Mapped[str] = mapped_column(String(20), index=True)          # FRENOS | SUSPENSION
    esquema: Mapped[str] = mapped_column(String(10))                   # viejo | nuevo | n_a
    nombre_archivo: Mapped[str] = mapped_column(String(255))
    ruta_archivo: Mapped[str] = mapped_column(String(500))
    fecha_prueba: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recibido_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_ahora, index=True
    )
    bytes: Mapped[int] = mapped_column(Integer, default=0)


class ArchivoImportado(Base):
    """Registro de qué archivos de `buffer_dir` ya se importaron, por nombre.

    El importador NUNCA mueve ni renombra archivos dentro de `buffer_dir` — esa
    carpeta la comparte la app emisora y su contenido no se toca. Para no
    reprocesar un archivo en cada revisión, se guarda aquí su nombre en cuanto
    se intenta importar (haya salido bien o mal).
    """

    __tablename__ = "archivos_importados"

    nombre_archivo: Mapped[str] = mapped_column(String(255), primary_key=True)
    estado: Mapped[str] = mapped_column(String(10))  # ok | error
    detalle: Mapped[str | None] = mapped_column(String(500), nullable=True)
    procesado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_ahora)
