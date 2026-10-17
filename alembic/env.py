import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from dotenv import load_dotenv

# Ensures Alembic can import the project modules (app/ folder)
sys.path.append(os.getcwd())

load_dotenv()

# Imports Base and ALL the models - Alembic uses this to know
# the "desired state" of the database and compare it with the current state.
from app.database import Base
from app.models.paciente import Paciente
from app.models.anamnese import Pergunta, Consulta, Resposta
from app.models.heredograma import Individuo, Relacionamento
from app.models.historico_clinico import (
    Alergia, Doenca, Cirurgia, HistoricoClinico, Operadora, PacienteConvenio
)
from app.models.cid import Cid
from app.models.profissional import Especialidade, Profissional
from app.models.log_auditoria import LogAuditoria
from app.models.encaminhamento import Encaminhamento
from app.models.exame import Exame
from app.models.perfil_acesso import Modulo, PerfilAcesso, PerfilAcessoModulo
from app.models.anexo import Anexo
from app.models.hipotese import HipoteseDiagnostica, FonteHipotese

config = context.config

# Uses the same database URL as the rest of the application (via .env, or the
# local SQLite default if no variable is set).
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./heredograma.db")
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()