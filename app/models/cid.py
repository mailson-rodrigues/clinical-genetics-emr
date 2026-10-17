from sqlalchemy import Column, Integer, String
from app.database import Base


class Cid(Base):
    """
    Catalog of CID codes (ICD - International Classification of Diseases),
    used to standardize the description of diseases in the system.
    """
    __tablename__ = "cids"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True, nullable=False)  # ex: "C61"
    descricao = Column(String, nullable=False)  # e.g. "Neoplasia maligna da próstata"
    capitulo = Column(String, nullable=True)  # ex: "Neoplasias"

    # Brazil still uses ICD-10 (the official migration to ICD-11 is
    # planned for January 2027, Technical Note 91/2024 of the Ministry
    # of Health) - field already prepared for that future transition, without
    # requiring schema rework when it arrives.
    versao = Column(String, nullable=False, default="CID-10", server_default="CID-10")