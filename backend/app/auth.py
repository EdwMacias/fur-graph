"""Sesión de navegador basada en cookie firmada, separada de la X-API-Key que
usa la aplicación emisora para hacer POST /api/pruebas.

El login (`POST /api/sesion`) valida la misma API key contra `settings.api_key`
y, si es correcta, emite una cookie httponly con un token `timestamp.firma`
firmado con HMAC-SHA256. No hay estado de sesión en el servidor: verificar la
cookie es solo comprobar la firma y que no haya expirado.
"""

import hashlib
import hmac
import time

from .config import settings

COOKIE_NAME = "fur_session"
MAX_AGE_SEG = 60 * 60 * 24 * 7  # 7 días


def _firmar(mensaje: str) -> str:
    return hmac.new(
        settings.session_secret_efectivo.encode(), mensaje.encode(), hashlib.sha256
    ).hexdigest()


def crear_token() -> str:
    ts = str(int(time.time()))
    return f"{ts}.{_firmar(ts)}"


def token_valido(token: str | None) -> bool:
    if not token or "." not in token:
        return False
    ts, firma = token.split(".", 1)
    if not hmac.compare_digest(firma, _firmar(ts)):
        return False
    try:
        return (time.time() - int(ts)) < MAX_AGE_SEG
    except ValueError:
        return False
