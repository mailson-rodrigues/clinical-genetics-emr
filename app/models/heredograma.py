from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from app.database import Base


class Individuo(Base):
    """
    Representa um indivíduo dentro do heredograma de uma consulta.
    O 'codigo' segue a notação do padrão PSTF/NSGC, ex: 'I.1', 'II.2'.
    """
    __tablename__ = "individuos"

    id = Column(Integer, primary_key=True, index=True)
    consulta_id = Column(Integer, ForeignKey("consultas.id"), nullable=False)

    codigo = Column(String, nullable=False)
    geracao = Column(Integer, nullable=False)
    posicao = Column(Integer, nullable=False)
    papel_descricao = Column(String, nullable=True)  # papel curto, ex: "Pai", "Avô paterno"
    observacao = Column(Text, nullable=True)  # informação clínica adicional, ex: "PSA alterado, em investigação"

    sexo = Column(String, nullable=False)
    afetado = Column(Boolean, default=False)
    portador = Column(Boolean, default=False)
    falecido = Column(Boolean, default=False)
    probando = Column(Boolean, default=False)

    cid_sugerido = Column(String, nullable=True)


class Relacionamento(Base):
    __tablename__ = "relacionamentos"

    id = Column(Integer, primary_key=True, index=True)
    consulta_id = Column(Integer, ForeignKey("consultas.id"), nullable=False)

    tipo = Column(String, nullable=False)
    origem_codigo = Column(String, nullable=False)
    destino_codigo = Column(String, nullable=False)
    consanguineo = Column(Boolean, default=False)