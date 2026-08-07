from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Exame(Base):
    """
    Representa a solicitação e o resultado de um exame no contexto de uma
    consulta, podendo ser vinculado a um indivíduo específico do
    heredograma (ex: familiar investigado) ou ao paciente/consulta em geral.
    """
    __tablename__ = "exames"

    id = Column(Integer, primary_key=True, index=True)
    consulta_id = Column(Integer, ForeignKey("consultas.id"), nullable=False)
    individuo_id = Column(Integer, ForeignKey("individuos.id"), nullable=True)
    profissional_id = Column(Integer, ForeignKey("profissionais.id"), nullable=True)  # quem registrou

    tipo_exame = Column(String, nullable=False)
    status = Column(String, nullable=False, default="solicitado")  # solicitado | em_andamento | concluido | cancelado

    data_solicitacao = Column(Date, nullable=True)
    data_resultado = Column(Date, nullable=True)
    resultado = Column(Text, nullable=True)
    observacoes = Column(Text, nullable=True)

    criado_em = Column(DateTime(timezone=True), server_default=func.now())
