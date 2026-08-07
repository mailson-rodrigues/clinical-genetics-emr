from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


# ---------- Itens clínicos genéricos (alergia, cirurgia, histórico) ----------

class ItemClinicoCreate(BaseModel):
    descricao: str


class ItemClinicoResponse(BaseModel):
    id: int
    paciente_id: int
    descricao: str
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Doença (com vínculo opcional a um código CID) ----------

class DoencaCreate(BaseModel):
    descricao: str
    cid_id: Optional[int] = None


class DoencaResponse(BaseModel):
    id: int
    paciente_id: int
    descricao: str
    cid_id: Optional[int] = None
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Operadoras (catálogo de convênios) ----------

class OperadoraCreate(BaseModel):
    nome: str


class OperadoraResponse(BaseModel):
    id: int
    nome: str

    model_config = ConfigDict(from_attributes=True)


# ---------- Vínculo paciente <-> convênio ----------

class PacienteConvenioCreate(BaseModel):
    operadora_id: int
    numero_carteirinha: Optional[str] = None


class PacienteConvenioResponse(BaseModel):
    id: int
    paciente_id: int
    operadora_id: int
    numero_carteirinha: Optional[str] = None
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)