from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración leída de variables de entorno (o de un archivo .env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Conexión a PostgreSQL. Ej: postgresql+psycopg://user:pass@db:5432/fur
    database_url: str = "postgresql+psycopg://fur:fur@localhost:5432/fur"

    # Token que debe enviar la aplicación emisora en el header X-API-Key.
    api_key: str = "cambia-esta-clave"

    # Directorio donde se guardan los JSON crudos (montar como volumen en prod).
    data_dir: str = "./data"

    # Directorio local donde la app emisora deja los FUR (frenos, suspensión,
    # alineación, ruidos) para que este servicio los importe automáticamente.
    buffer_dir: str = "/home/cedac/app/buffer_pruebas"

    # Cada cuántos segundos se revisa `buffer_dir` en busca de archivos nuevos.
    buffer_intervalo_seg: int = 15

    # Orígenes permitidos para CORS, separados por coma. "*" permite todos.
    cors_origins: str = "*"

    # Series más largas que este umbral se submuestrean antes de enviarlas.
    downsample_umbral: int = 1500

    # Secreto para firmar la cookie de sesión (login con API key). Si se deja
    # el valor por defecto, usa la propia API key — cámbialo en prod.
    session_secret: str = ""

    # Poner en True detrás de HTTPS para que la cookie de sesión solo viaje por TLS.
    cookie_secure: bool = False

    @property
    def session_secret_efectivo(self) -> str:
        return self.session_secret or self.api_key

    @property
    def cors_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return origins or ["*"]


settings = Settings()
