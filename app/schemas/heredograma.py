from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class IndividuoExtraido(BaseModel):
    codigo: str
    geracao: int
    posicao: int
    papel_descricao: Optional[str] = None
    observacao: Optional[str] = None
    sexo: str
    afetado: bool = False
    portador: bool = False
    falecido: bool = False
    probando: bool = False
    cid_sugerido: Optional[str] = None


class RelacionamentoExtraido(BaseModel):
    tipo: str
    origem_codigo: str
    destino_codigo: str
    consanguineo: bool = False


class HeredogramaExtraido(BaseModel):
    individuos: List[IndividuoExtraido]
    relacionamentos: List[RelacionamentoExtraido]


class IndividuoResponse(IndividuoExtraido):
    id: int
    consulta_id: int

    model_config = ConfigDict(from_attributes=True)


class RelacionamentoResponse(RelacionamentoExtraido):
    id: int
    consulta_id: int

    model_config = ConfigDict(from_attributes=True)


class HeredogramaResponse(BaseModel):
    consulta_id: int
    individuos: List[IndividuoResponse]
    relacionamentos: List[RelacionamentoResponse]