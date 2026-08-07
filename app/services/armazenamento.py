import os
import uuid
from pathlib import Path

# Path relativo à raiz do projeto (mesma convenção do DATABASE_URL padrão
# em app/database.py) - fora de frontend/, para não ficar acessível sem
# autenticação via o mount de arquivos estáticos (StaticFiles em
# app/main.py só serve frontend/). Configurável via env var UPLOAD_DIR
# para os testes isolarem os arquivos gerados num diretório próprio (ver
# tests/conftest.py e tests_e2e/conftest.py) - módulo lido dinamicamente
# (não importado por nome) por quem usa, para o monkeypatch dos testes
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
    Nome único gerado (uuid4 + extensão derivada do tipo de conteúdo, não
    do nome original enviado) - nunca o nome original diretamente como
    nome em disco, para evitar colisão e path traversal.
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
