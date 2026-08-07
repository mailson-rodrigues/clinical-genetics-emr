from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.database import Base


class Modulo(Base):
    """
    Catálogo fixo de módulos do sistema, usado para compor perfis de
    acesso granulares (ex: "pacientes", "consultas"). Definido pelo
    sistema, não pelo usuário - sem rota de criação, só GET /modulos/.
    """
    __tablename__ = "modulos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False)
    nome = Column(String, nullable=False)


class PerfilAcesso(Base):
    """
    Perfil de acesso reutilizável (ex: "Recepcionista"), atribuível a
    profissionais não-administradores para dar controle fino sobre
    quais módulos eles podem acessar. Administrador sempre tem acesso
    total, independente de perfil (ver exigir_acesso_modulo em
    app/dependencies.py).
    """
    __tablename__ = "perfis_acesso"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, nullable=False)
    descricao = Column(Text, nullable=True)


class PerfilAcessoModulo(Base):
    """Vínculo N:N entre um perfil de acesso e os módulos liberados para ele."""
    __tablename__ = "perfil_acesso_modulos"

    id = Column(Integer, primary_key=True, index=True)
    perfil_acesso_id = Column(Integer, ForeignKey("perfis_acesso.id"), nullable=False)
    modulo_id = Column(Integer, ForeignKey("modulos.id"), nullable=False)
