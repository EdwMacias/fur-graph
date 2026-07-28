from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import Base, engine
from .routers import pruebas


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crea las tablas si no existen (suficiente para este esquema simple).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="FUR Graph API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pruebas.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
