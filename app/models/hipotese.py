from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class HipoteseDiagnostica(Base):
    """
    Hipótese diagnóstica gerada por IA (com busca na web) a partir das
    respostas da anamnese de uma consulta.
    """
    __tablename__ = "hipoteses_diagnosticas"

    id = Column(Integer, primary_key=True, index=True)
    consulta_id = Column(Integer, ForeignKey("consultas.id"), nullable=False)
    condicao = Column(String, nullable=False)
    justificativa = Column(Text, nullable=False)
    cid_sugerido = Column(String, nullable=True)  # ex: "C61" - null se a IA não tiver confiança
    ordem = Column(Integer, nullable=False)  # 1 = hipótese mais provável, na ordem devolvida pela IA
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    fontes = relationship(
        "FonteHipotese", back_populates="hipotese", cascade="all, delete-orphan"
    )


class FonteHipotese(Base):
    """
    Fonte/artigo científico (PubMed, SciELO, Google Acadêmico, OMIM,
    Orphanet, GARD/NIH, MedlinePlus) que a IA consultou para embasar
    uma hipótese diagnóstica. Tabela relacionada (em vez de um campo de
    texto solto) para poder controlar quantidade e adicionar mais depois
    (ver POST .../mais-fontes).
    """
    __tablename__ = "fontes_hipoteses"

    id = Column(Integer, primary_key=True, index=True)
    hipotese_id = Column(Integer, ForeignKey("hipoteses_diagnosticas.id"), nullable=False)
    titulo = Column(String, nullable=True)
    url = Column(String, nullable=False)
    origem = Column(String, nullable=False)  # ex: "PubMed", "SciELO", "OMIM"

    hipotese = relationship("HipoteseDiagnostica", back_populates="fontes")
