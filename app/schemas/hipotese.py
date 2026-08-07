from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional


class FonteHipoteseExtraida(BaseModel):
    titulo: Optional[str] = None
    url: str
    origem: str


class FonteHipoteseResponse(BaseModel):
    id: int
    titulo: Optional[str] = None
    url: str
    origem: str

    model_config = ConfigDict(from_attributes=True)


class HipoteseDiagnosticaExtraida(BaseModel):
    condicao: str
    justificativa: str
    cid_sugerido: Optional[str] = None
    fontes: List[FonteHipoteseExtraida] = []


class HipotesesExtraidas(BaseModel):
    hipoteses: List[HipoteseDiagnosticaExtraida]


class HipoteseDiagnosticaResponse(BaseModel):
    id: int
    consulta_id: int
    condicao: str
    justificativa: str
    cid_sugerido: Optional[str] = None
    ordem: int
    criado_em: datetime
    fontes: List[FonteHipoteseResponse] = []

    model_config = ConfigDict(from_attributes=True)
