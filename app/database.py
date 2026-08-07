import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Em desenvolvimento local, sem nenhuma configuração extra, usamos SQLite
# (arquivo "heredograma.db"). Em produção, defina DATABASE_URL no .env
# apontando para um Postgres, no formato:
#   postgresql://usuario:senha@host:porta/nome_banco
# e rode `alembic upgrade head` para criar as tabelas lá - o restante do
# código (models, rotas, Alembic) não precisa de nenhuma alteração.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./heredograma.db")

# "check_same_thread" só existe/faz sentido para SQLite; passar isso para
# o driver do Postgres (psycopg2) causaria erro de conexão.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# "engine" é a conexão com o banco de dados
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# "SessionLocal" é usado para abrir conversas (sessões) com o banco a cada requisição
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# "Base" é a classe da qual todos os nossos modelos (tabelas) vão herdar
Base = declarative_base()


def get_db():
    """
    Fornece uma sessão de banco de dados para cada requisição da API
    e garante que ela seja fechada corretamente depois.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()