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

    # Orígenes permitidos para CORS, separados por coma. "*" permite todos.
    cors_origins: str = "*"

    # Series más largas que este umbral se submuestrean antes de enviarlas.
    downsample_umbral: int = 1500

    @property
    def cors_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return origins or ["*"]


settings = Settings()
