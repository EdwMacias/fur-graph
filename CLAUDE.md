# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es

Visor web de pruebas FUR (frenos y suspensión de vehículos). Otra aplicación envía JSON de
pruebas por `POST /api/pruebas`; este servicio los guarda, lista y grafica.

El código, los comentarios y los nombres de identificadores están **en español**. Mantén esa
convención al añadir código (`pruebas`, `paneles`, `metricas`, `muestras`, `valores`, `esquema`).

## Comandos

```bash
# Backend (requiere Postgres accesible)
cd backend && pip install -r requirements.txt
API_KEY=dev DATABASE_URL=postgresql+psycopg://fur:fur@localhost:5432/fur DATA_DIR=./data \
  uvicorn app.main:app --reload          # :8000, docs en /docs

# Frontend
cd frontend && npm install
npm run dev                              # :5173, proxy /api -> localhost:8000
npm run build

# Stack completo
cp .env.example .env && docker compose up -d --build   # api :8000, web :8080
```

No hay tests ni linters configurados en el repo.

## Arquitectura

Tres capas con una separación deliberada de responsabilidades:

1. **Almacenamiento dual** (`backend/app/storage.py` + `models.py`): el JSON crudo se escribe
   íntegro en `DATA_DIR` (volumen `fur_data` en prod); Postgres guarda **solo metadatos**
   (`Prueba`: tipo, esquema, ruta_archivo, fechas, bytes). Ninguna serie de datos vive en la DB.
   Las tablas se crean con `Base.metadata.create_all` en el `lifespan` de `main.py` — no hay
   migraciones; cambiar `models.py` requiere recrear la tabla a mano.

2. **`backend/app/parsing.py` es el núcleo del proyecto.** Detecta el esquema y normaliza
   cualquier FUR a una única forma `{tipo, esquema, id_prueba, fecha, paneles[], metricas{}}`.
   Cada panel lleva `series` (muestras/valores), `lineas` (referencias horizontales con etiqueta
   ya formateada) y `marcadores` (puntos destacados). El frontend es genérico: dibuja lo que
   venga en `paneles` sin conocer frenos ni suspensión, así que **añadir un esquema nuevo es
   trabajo solo de `parsing.py`**.

3. **Frontend** (`frontend/src`): Vue 3 + vue-router, dos vistas (`ListaView`, `DetalleView`) y
   `GraficoLinea.vue`, que traduce un panel normalizado a datasets de Chart.js (las `lineas` se
   emiten como datasets de dos puntos que abarcan el rango X, no como anotaciones).

### Detección de esquemas (`parsing.detectar`)

- `SuspensionDinamicaEje1`/`SuspensionEstaticaEje1` presentes → `SUSPENSION` / `n_a`
- `FuerzasEjes.FuerzasEje1_Izq` → `FRENOS` / `nuevo` (split izq/der + `FuerzasAuxiliarEje2_*`)
- `FuerzasEjes.FuerzasEje1` → `FRENOS` / `viejo`

Cualquier otra cosa lanza `ValueError` → HTTP 400 en la ingesta.

### Paridad con los scripts de referencia

`graficar_frenos.py`, `graficar_suspension.py` y `visor_frenos.py` (raíz del repo, matplotlib/
tkinter) son la **especificación de las métricas**. `parsing.py` replica sus fórmulas y esas
diferencias sutiles son intencionales:

- FRENOS nuevo usa `fuerza_maxima_abs` (máximo en valor absoluto, con su nº de muestra); FRENOS
  viejo usa `maximo` simple, igual que `visor_frenos.py`.
- `eficacia_total = Σ|F_max| / peso_total * 100`, con `peso_total` = suma de los cuatro promedios
  estáticos. `eficacia_auxiliar` usa solo las fuerzas auxiliares del eje 2.

Si cambias una métrica, verifica contra el script correspondiente usando los JSON de ejemplo de
la raíz (`3_FRENOS_*.json`, `45_FRENOS_*.json`, `3_SUSPENSION_*.json` — viejo, nuevo y suspensión
respectivamente).

### Downsampling

Las series de suspensión son enormes (~3 MB por archivo), así que `_serie(..., reducir=True)`
aplica LTTB reduciendo a `DOWNSAMPLE_UMBRAL` puntos (def. 1500) conservando la forma de la curva.
Las series de frenos **no** se reducen. El downsampling ocurre en cada request a `/datos`; no hay
caché.

## Detalles a tener en cuenta

- La ingesta acepta multipart (`file`) **o** el JSON crudo en el body, y desenvuelve arrays de un
  elemento (`data[0]`) — varios FUR llegan envueltos en una lista.
- `X-API-Key` protege **solo** el POST de ingesta; los GET son públicos. La clave se compara con
  `settings.api_key`.
- El frontend pide la API key al usuario en `SubirFur.vue`; no se persiste.
- `VITE_API_BASE` es **build-time** (se hornea en el bundle vía `ARG` del Dockerfile). Cambiarlo
  en producción exige rebuild del servicio `web`.
- Si el archivo de datos falta en disco, `/datos` responde 410 (no 404, que significa "no existe
  la prueba en la DB").
