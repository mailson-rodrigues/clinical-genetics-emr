from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


# ---------- Generic clinical items (allergy, surgery, history) ----------

class ItemClinicoCreate(BaseModel):
    descricao: str


class ItemClinicoResponse(BaseModel):
    id: int
    paciente_id: int
    descricao: str
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Disease (with optional link to a CID code) ----------

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


# ---------- Insurers (health plan catalog) ----------

class OperadoraCreate(BaseModel):
    nome: str


class OperadoraResponse(BaseModel):
    id: int
    nome: str

    model_config = ConfigDict(from_attributes=True)


# ---------- Patient <-> health plan link ----------

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