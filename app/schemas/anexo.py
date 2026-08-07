from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class AnexoResponse(BaseModel):
    id: int
    paciente_id: Optional[int] = None
    exame_id: Optional[int] = None
    profissional_id: Optional[int] = None
    nome_original: str
    tipo_conteudo: str
    tamanho_bytes: int
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
