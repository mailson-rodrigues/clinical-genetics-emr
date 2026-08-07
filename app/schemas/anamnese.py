from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


class PerguntaResponse(BaseModel):
    id: int
    codigo: str
    categoria: str
    texto: str
    ordem: int

    model_config = ConfigDict(from_attributes=True)


class ConsultaCreate(BaseModel):
    paciente_id: int
    condicao_investigada: str
    # profissional_id NAO e enviado pelo cliente - e definido automaticamente
    # a partir do token de autenticacao (ver app/routes/consulta.py)


class ConsultaUpdate(BaseModel):
    condicao_investigada: Optional[str] = None
    status: Optional[str] = None


class ConsultaResponse(BaseModel):
    id: int
    paciente_id: int
    profissional_id: Optional[int] = None
    condicao_investigada: str
    status: str
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class RespostaCreate(BaseModel):
    pergunta_id: int
    resposta_texto: str


class RespostaUpdate(BaseModel):
    resposta_texto: str


class RespostaResponse(BaseModel):
    id: int
    consulta_id: int
    pergunta_id: int
    resposta_texto: str
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsultaComRespostas(ConsultaResponse):
    respostas: List[RespostaResponse] = []