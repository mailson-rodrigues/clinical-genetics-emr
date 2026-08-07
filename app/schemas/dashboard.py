from pydantic import BaseModel
from datetime import datetime
from typing import List


class AtividadeRecente(BaseModel):
    consulta_id: int
    paciente_nome: str
    condicao_investigada: str
    criado_em: datetime


class ResumoDashboard(BaseModel):
    total_pacientes_ativos: int
    consultas_mes_atual: int
    encaminhamentos_pendentes: int
    exames_aguardando: int
    atividade_recente: List[AtividadeRecente]
