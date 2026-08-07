from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Pergunta(Base):
    __tablename__ = "perguntas"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True, nullable=False)
    categoria = Column(String, nullable=False)
    texto = Column(Text, nullable=False)
    ordem = Column(Integer, nullable=False)


class Consulta(Base):
    __tablename__ = "consultas"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    profissional_id = Column(Integer, ForeignKey("profissionais.id"), nullable=True)  # preenchido no login futuramente
    condicao_investigada = Column(String, nullable=False)
    status = Column(String, nullable=False, default="em_andamento")
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    respostas = relationship("Resposta", back_populates="consulta", cascade="all, delete-orphan")


class Resposta(Base):
    __tablename__ = "respostas"

    id = Column(Integer, primary_key=True, index=True)
    consulta_id = Column(Integer, ForeignKey("consultas.id"), nullable=False)
    pergunta_id = Column(Integer, ForeignKey("perguntas.id"), nullable=False)
    resposta_texto = Column(Text, nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    consulta = relationship("Consulta", back_populates="respostas")
    pergunta = relationship("Pergunta")