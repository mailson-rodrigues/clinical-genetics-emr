from sqlalchemy import Column, Integer, String
from app.database import Base


class Cid(Base):
    """
    Catálogo de códigos CID (Classificação Internacional de Doenças),
    usado para padronizar a descrição de doenças no sistema.
    """
    __tablename__ = "cids"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True, nullable=False)  # ex: "C61"
    descricao = Column(String, nullable=False)  # ex: "Neoplasia maligna da próstata"
    capitulo = Column(String, nullable=True)  # ex: "Neoplasias"

    # O Brasil ainda usa CID-10 (a migração oficial para CID-11 está
    # prevista para janeiro de 2027, Nota Técnica 91/2024 do Ministério
    # da Saúde) - campo já preparado para essa transição futura, sem
    # exigir retrabalho de schema quando ela chegar.
    versao = Column(String, nullable=False, default="CID-10", server_default="CID-10")