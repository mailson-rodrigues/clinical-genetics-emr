from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Especialidade(Base):
    __tablename__ = "especialidades"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, nullable=False)


class Profissional(Base):
    """
    Representa um profissional de saúde com acesso ao sistema.
    nivel_acesso: "profissional" (padrão) ou "administrador".
    """
    __tablename__ = "profissionais"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    especialidade_id = Column(Integer, ForeignKey("especialidades.id"), nullable=True)
    registro_profissional = Column(String, nullable=True)
    nivel_acesso = Column(String, nullable=False, default="profissional")
    # Só é usado por profissionais não-administradores - administrador
    # sempre tem acesso total, independente de perfil (ver
    # exigir_acesso_modulo em app/dependencies.py).
    perfil_acesso_id = Column(Integer, ForeignKey("perfis_acesso.id"), nullable=True)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())