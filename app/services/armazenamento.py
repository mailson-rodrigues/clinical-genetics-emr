import os
import uuid
from pathlib import Path

# Path relative to the project root (same convention as the default DATABASE_URL
# in app/database.py) - outside frontend/, so it is not reachable without
# authentication through the static files mount (StaticFiles in
# app/main.py only serves frontend/). Configurable via the UPLOAD_DIR env var
# so the tests can isolate the generated files in their own directory (see
# tests/conftest.py and tests_e2e/conftest.py) - module read dynamically
# (not imported by name) by whoever uses it, for the tests' monkeypatch
# funcionar.
DIRETORIO_UPLOADS = Path(os.getenv("UPLOAD_DIR", "uploads"))

TIPOS_PERMITIDOS = {"application/pdf", "image/jpeg", "image/png"}
TAMANHO_MAXIMO_BYTES = 10 * 1024 * 1024  # 10MB

_EXTENSAO_POR_TIPO = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


def gerar_nome_armazenado(tipo_conteudo: str) -> str:
    """
    Generated unique name (uuid4 + extension derived from the content type, not
    from the original uploaded name) - never the original name directly as
    the name on disk, to avoid collisions and path traversal.
    """
    extensao = _EXTENSAO_POR_TIPO[tipo_conteudo]
    return f"{uuid.uuid4()}{extensao}"


def salvar_arquivo(conteudo: bytes, nome_armazenado: str) -> None:
    DIRETORIO_UPLOADS.mkdir(parents=True, exist_ok=True)
    caminho = DIRETORIO_UPLOADS / nome_armazenado
    with open(caminho, "wb") as arquivo:
        arquivo.write(conteudo)


def caminho_completo(nome_armazenado: str) -> Path:
    return DIRETORIO_UPLOADS / nome_armazenado


def remover_arquivo(nome_armazenado: str) -> None:
    caminho = caminho_completo(nome_armazenado)
    if caminho.exists():
        caminho.unlink()
