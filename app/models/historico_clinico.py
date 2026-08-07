from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Alergia(Base):
    __tablename__ = "alergias"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    descricao = Column(Text, nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())


class Doenca(Base):
    __tablename__ = "doencas"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    cid_id = Column(Integer, ForeignKey("cids.id"), nullable=True)  # vínculo opcional com o catálogo CID
    descricao = Column(Text, nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())


class Cirurgia(Base):
    __tablename__ = "cirurgias"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    descricao = Column(Text, nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())


class HistoricoClinico(Base):
    __tablename__ = "historicos_clinicos"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    descricao = Column(Text, nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())


class Operadora(Base):
    __tablename__ = "operadoras"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, nullable=False)


class PacienteConvenio(Base):
    __tablename__ = "paciente_convenios"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    operadora_id = Column(Integer, ForeignKey("operadoras.id"), nullable=False)
    numero_carteirinha = Column(String, nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())