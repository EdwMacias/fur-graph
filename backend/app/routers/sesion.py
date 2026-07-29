from fastapi import APIRouter, Header, HTTPException, Request, Response

from .. import auth
from ..config import settings

router = APIRouter(prefix="/api/sesion", tags=["sesion"])


@router.post("")
def iniciar(response: Response, x_api_key: str | None = Header(default=None)):
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="API key inválida o ausente")
    response.set_cookie(
        auth.COOKIE_NAME,
        auth.crear_token(),
        max_age=auth.MAX_AGE_SEG,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
    )
    return {"ok": True}


@router.delete("")
def cerrar(response: Response):
    response.delete_cookie(auth.COOKIE_NAME)
    return {"ok": True}


@router.get("")
def estado(request: Request):
    return {"autenticado": auth.token_valido(request.cookies.get(auth.COOKIE_NAME))}
