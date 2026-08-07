from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class EncaminhamentoCreate(BaseModel):
    especialidade_id: Optional[int] = None
    motivo: str


class EncaminhamentoUpdate(BaseModel):
    status: Optional[str] = None  # "pendente" | "concluido" | "cancelado"
    motivo: Optional[str] = None
    especialidade_id: Optional[int] = None


class EncaminhamentoResponse(BaseModel):
    id: int
    consulta_id: int
    especialidade_id: Optional[int] = None
    profissional_id: Optional[int] = None
    motivo: str
    status: str
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)