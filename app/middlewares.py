from fastapi import Request
from jose import JWTError

from app.database import SessionLocal
from app.models.log_auditoria import LogAuditoria
from app.services.seguranca import decodificar_token

# Extensions/routes that do NOT generate logs (the frontend static files and
# the automatic Swagger documentation) - avoids polluting the log with noise.
EXTENSOES_IGNORADAS = (".html", ".js", ".css", ".svg", ".png", ".jpg", ".ico")
PREFIXOS_IGNORADOS = ("/docs", "/openapi", "/redoc")


async def middleware_log_auditoria(request: Request, call_next):
    """
    Middleware that automatically logs EVERY relevant call made
    to the API: who made it (if authenticated), HTTP method, path, and the response
    status. Runs on every request, without needing to instrument each
    route manually.
    """
    caminho = request.url.path

    deve_logar = (
        caminho != "/"
        and not caminho.startswith(PREFIXOS_IGNORADOS)
        and not caminho.endswith(EXTENSOES_IGNORADAS)
    )

    resposta = await call_next(request)

    if deve_logar:
        profissional_id = None
        cabecalho_auth = request.headers.get("authorization")
        if cabecalho_auth and cabecalho_auth.startswith("Bearer "):
            token = cabecalho_auth.removeprefix("Bearer ").strip()
            try:
                payload = decodificar_token(token)
                profissional_id = payload.get("profissional_id")
            except JWTError:
                profissional_id = None  # token invalido/expirado - loga como anonimo

        db = SessionLocal()
        try:
            novo_log = LogAuditoria(
                profissional_id=profissional_id,
                metodo=request.method,
                caminho=caminho,
                status_code=resposta.status_code,
            )
            db.add(novo_log)
            db.commit()
        finally:
            db.close()

    return resposta