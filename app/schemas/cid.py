from pydantic import BaseModel, ConfigDict
from typing import Optional


class CidCreate(BaseModel):
    codigo: str
    descricao: str
    capitulo: Optional[str] = None
    versao: str = "CID-10"


class CidResponse(BaseModel):
    id: int
    codigo: str
    descricao: str
    capitulo: Optional[str] = None
    versao: str

    model_config = ConfigDict(from_attributes=True)