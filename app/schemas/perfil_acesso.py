from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class ModuloResponse(BaseModel):
    id: int
    codigo: str
    nome: str

    model_config = ConfigDict(from_attributes=True)


class PerfilAcessoCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None


class PerfilAcessoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None


class PerfilAcessoResponse(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None
    modulos: List[ModuloResponse] = []

    model_config = ConfigDict(from_attributes=True)


class VincularModuloRequest(BaseModel):
    modulo_id: int
