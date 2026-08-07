from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional


class ExameCreate(BaseModel):
    individuo_id: Optional[int] = None
    tipo_exame: str
    status: Optional[str] = None  # "solicitado" | "em_andamento" | "concluido" | "cancelado"
    data_solicitacao: Optional[date] = None
    resultado: Optional[str] = None
    observacoes: Optional[str] = None


class ExameUpdate(BaseModel):
    individuo_id: Optional[int] = None
    tipo_exame: Optional[str] = None
    status: Optional[str] = None
    data_solicitacao: Optional[date] = None
    data_resultado: Optional[date] = None
    resultado: Optional[str] = None
    observacoes: Optional[str] = None


class ExameResponse(BaseModel):
    id: int
    consulta_id: int
    individuo_id: Optional[int] = None
    profissional_id: Optional[int] = None
    tipo_exame: str
    status: str
    data_solicitacao: Optional[date] = None
    data_resultado: Optional[date] = None
    resultado: Optional[str] = None
    observacoes: Optional[str] = None
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
