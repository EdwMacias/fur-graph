import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import importador
from .config import settings
from .db import Base, engine
from .routers import pruebas, sesion

logger = logging.getLogger(__name__)


async def _bucle_importador():
    while True:
        try:
            await asyncio.to_thread(importador.escanear_buffer)
        except Exception:
            logger.exception("Error revisando buffer_dir")
        await asyncio.sleep(settings.buffer_intervalo_seg)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crea las tablas si no existen (suficiente para este esquema simple).
    Base.metadata.create_all(bind=engine)
    tarea = asyncio.create_task(_bucle_importador())
    yield
    tarea.cancel()


app = FastAPI(title="FUR Graph API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pruebas.router)
app.include_router(sesion.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
