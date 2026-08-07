from fastapi import Request
from jose import JWTError

from app.database import SessionLocal
from app.models.log_auditoria import LogAuditoria
from app.services.seguranca import decodificar_token

# Extensões/rotas que NÃO geram log (arquivos estáticos do frontend e
# documentação automática do Swagger) - evita poluir o log com ruído.
EXTENSOES_IGNORADAS = (".html", ".js", ".css", ".svg", ".png", ".jpg", ".ico")
PREFIXOS_IGNORADOS = ("/docs", "/openapi", "/redoc")


async def middleware_log_auditoria(request: Request, call_next):
    """
    Middleware que registra automaticamente TODA chamada relevante feita
    à API: quem fez (se autenticado), método HTTP, caminho, e o status
    de resposta. Roda em toda requisição, sem precisar instrumentar cada
    rota manualmente.
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