# Visor FUR — Frenos y Suspensión

Servicio web para recibir pruebas FUR (JSON) desde otra aplicación, guardarlas, listarlas
conforme llegan y graficarlas replicando lo que hacen los scripts `graficar_frenos.py`,
`graficar_suspension.py` y `visor_frenos.py`.

- **Backend:** FastAPI + PostgreSQL (solo metadatos) + JSON crudo en disco.
- **Frontend:** Vite + Vue 3 + vue-chartjs.
- **Despliegue:** Docker / Dokploy (expone API y frontend).

## Arquitectura

```
otra app  --POST /api/pruebas (X-API-Key)-->  FastAPI  --guarda JSON-->  /data (volumen)
                                                  |--metadatos-->  PostgreSQL
frontend (Vue)  --GET /api/pruebas, /datos-->  FastAPI  --normaliza+downsample-->  charts
```

El JSON crudo se guarda íntegro en `DATA_DIR`; Postgres solo indexa metadatos (tipo, esquema,
fechas, tamaño). El endpoint `/datos` lee el archivo, calcula las métricas y devuelve las series
listas para graficar (con submuestreo LTTB para las series densas de suspensión).

## Esquemas soportados (auto-detectados)

- **FRENOS viejo:** `PesosEjes.{PesosEje1,PesosEje2}`, `FuerzasEjes.{FuerzasEje1,FuerzasEje2}`.
- **FRENOS nuevo:** split `_Izq`/`_Der` + `FuerzasAuxiliarEje2_*` (eficacia total y auxiliar).
- **SUSPENSION:** `SuspensionEstatica/DinamicaEje1/2.{Izquierdo,Derecho}`.

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/pruebas` | Ingesta. Header `X-API-Key`. Acepta multipart `file` o JSON crudo en el body. |
| GET | `/api/pruebas?tipo=&limit=&offset=` | Lista metadatos (más recientes primero). |
| GET | `/api/pruebas/{id}` | Metadatos de una prueba. |
| GET | `/api/pruebas/{id}/datos` | Paneles + series + métricas para graficar. |
| GET | `/api/pruebas/{id}/raw` | Descarga el JSON original. |
| GET | `/api/health` | Healthcheck. |

Ejemplo de ingesta:

```bash
curl -H "X-API-Key: TU_CLAVE" \
     -F "file=@45_FRENOS_20260507091203.json" \
     http://localhost:8000/api/pruebas
# o con el JSON en el body:
curl -H "X-API-Key: TU_CLAVE" -H "Content-Type: application/json" \
     --data-binary @3_SUSPENSION_20260423153521.json \
     http://localhost:8000/api/pruebas
```

## Desarrollo local

Backend (necesita un Postgres accesible en `DATABASE_URL`):

```bash
cd backend
pip install -r requirements.txt
export API_KEY=dev  DATABASE_URL=postgresql+psycopg://fur:fur@localhost:5432/fur  DATA_DIR=./data
uvicorn app.main:app --reload
```

Frontend (proxy a `http://localhost:8000` por defecto):

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

## Producción con Docker / Dokploy

```bash
cp .env.example .env   # edita API_KEY, contraseñas, CORS_ORIGINS
docker compose up -d --build
```

Un solo dominio: nginx del servicio `web` sirve la SPA y reenvía `/api/` a `api:8000`, así que
**no hace falta publicar ni exponer la API en otro dominio**. Ningún servicio publica puertos en
el host; Traefik/Dokploy entra por la red interna.

En Dokploy: crea la app desde este repo/compose, define las variables de entorno de `.env`, y
mapea el dominio (`grafica.cedac.gov.co`) al servicio **`web`, puerto `80`** — apuntar a 8080 da
`502 Bad Gateway` porque nginx escucha en el 80. Deja `VITE_API_BASE` **vacío** (si lo pones a
`http://localhost:8000` el navegador del usuario pedirá a su propia máquina). Solo rellénalo si
algún día la API vive en otro dominio, y recuerda que es build-time: exige rebuild del servicio
`web`. Pon `CORS_ORIGINS` al dominio del frontend. El volumen `fur_data` persiste los JSON crudos; `db_data`
persiste Postgres. Si prefieres usar el Postgres gestionado de Dokploy, elimina el servicio `db`
del compose y apunta `DATABASE_URL` a esa base.

## Variables de entorno

| Variable | Dónde | Descripción |
|----------|-------|-------------|
| `API_KEY` | api | Token exigido en `X-API-Key` para ingesta. |
| `DATABASE_URL` | api | Cadena SQLAlchemy a Postgres (`postgresql+psycopg://...`). |
| `DATA_DIR` | api | Directorio de los JSON crudos (volumen). |
| `CORS_ORIGINS` | api | Orígenes permitidos, separados por coma (`*` = todos). |
| `DOWNSAMPLE_UMBRAL` | api | Máx. puntos por serie antes de submuestrear (def. 1500). |
| `VITE_API_BASE` | web (build) | Dominio de la API para el frontend. Vacío si comparten host. |

## Nota sobre el "enlace" de la otra aplicación

Se asume que la otra app hace un `POST` a `/api/pruebas` con la API key. Si en su lugar entrega
una URL para que este servicio descargue el FUR, se puede añadir un endpoint
`POST /api/pruebas/desde-url` sin cambiar el resto.
