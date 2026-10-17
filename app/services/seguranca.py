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
    """Turns a plain-text password into a secure hash to store in the database."""
    return contexto_senha.hash(senha_texto_puro)


def verificar_senha(senha_texto_puro: str, senha_hash: str) -> bool:
    """Checks whether a typed password matches the hash stored in the database."""
    return contexto_senha.verify(senha_texto_puro, senha_hash)


def criar_token_acesso(dados: dict) -> str:
    """Generates a signed JWT token, containing the given data + an expiration date."""
    dados_para_codificar = dados.copy()
    expira_em = datetime.now(timezone.utc) + timedelta(minutes=EXPIRACAO_TOKEN_MINUTOS)
    dados_para_codificar.update({"exp": expira_em})
    return jwt.encode(dados_para_codificar, CHAVE_SECRETA, algorithm=ALGORITMO)


def decodificar_token(token: str) -> dict:
    """
    Decodes and validates a JWT token. Raises jose.JWTError if the token is
    invalid, tampered with, or expired.
    """
    return jwt.decode(token, CHAVE_SECRETA, algorithms=[ALGORITMO])