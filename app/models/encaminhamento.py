from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Encaminhamento(Base):
    """
    Represents the referral of a patient (in the context of a
    consultation) to another specialist, based on the findings of the
    genetic counseling.
    """
    __tablename__ = "encaminhamentos"

    id = Column(Integer, primary_key=True, index=True)
    consulta_id = Column(Integer, ForeignKey("consultas.id"), nullable=False)
    especialidade_id = Column(Integer, ForeignKey("especialidades.id"), nullable=True)
    profissional_id = Column(Integer, ForeignKey("profissionais.id"), nullable=True)  # quem encaminhou

    motivo = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="pendente")  # pendente | concluido | cancelado

    criado_em = Column(DateTime(timezone=True), server_default=func.now())