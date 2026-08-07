import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from jose import jwt, JWTError
from passlib.context import CryptContext

load_dotenv()

contexto_senha = CryptContext(schemes=["bcrypt"], deprecated="auto")

CHAVE_SECRETA = os.getenv("JWT_SECRET_KEY", "chave-temporaria-trocar-no-env")
ALGORITMO = "HS256"
EXPIRACAO_TOKEN_MINUTOS = 480  # 8 horas


def gerar_hash_senha(senha_texto_puro: str) -> str:
    """Transforma uma senha em texto puro em um hash seguro para salvar no banco."""
    return contexto_senha.hash(senha_texto_puro)


def verificar_senha(senha_texto_puro: str, senha_hash: str) -> bool:
    """Confere se uma senha digitada bate com o hash salvo no banco."""
    return contexto_senha.verify(senha_texto_puro, senha_hash)


def criar_token_acesso(dados: dict) -> str:
    """Gera um token JWT assinado, contendo os dados informados + data de expiração."""
    dados_para_codificar = dados.copy()
    expira_em = datetime.now(timezone.utc) + timedelta(minutes=EXPIRACAO_TOKEN_MINUTOS)
    dados_para_codificar.update({"exp": expira_em})
    return jwt.encode(dados_para_codificar, CHAVE_SECRETA, algorithm=ALGORITMO)


def decodificar_token(token: str) -> dict:
    """
    Decodifica e valida um token JWT. Lança jose.JWTError se o token for
    inválido, adulterado, ou estiver expirado.
    """
    return jwt.decode(token, CHAVE_SECRETA, algorithms=[ALGORITMO])