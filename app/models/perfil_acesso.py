from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.database import Base


class Modulo(Base):
    """
    Fixed catalog of system modules, used to compose granular access
    profiles (e.g. "pacientes", "consultas"). Defined by the
    system, not by the user - no create route, only GET /modulos/.
    """
    __tablename__ = "modulos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False)
    nome = Column(String, nullable=False)


class PerfilAcesso(Base):
    """
    Reusable access profile (e.g. "Recepcionista"), assignable to
    non-administrator professionals to give fine-grained control over
    which modules they can access. An administrator always has full
    access, regardless of profile (see exigir_acesso_modulo in
    app/dependencies.py).
    """
    __tablename__ = "perfis_acesso"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, nullable=False)
    descricao = Column(Text, nullable=True)


class PerfilAcessoModulo(Base):
    """N:N link between an access profile and the modules released for it."""
    __tablename__ = "perfil_acesso_modulos"

    id = Column(Integer, primary_key=True, index=True)
    perfil_acesso_id = Column(Integer, ForeignKey("perfis_acesso.id"), nullable=False)
    modulo_id = Column(Integer, ForeignKey("modulos.id"), nullable=False)
