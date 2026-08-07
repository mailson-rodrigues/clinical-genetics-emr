from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class LogAuditoriaResponse(BaseModel):
    id: int
    profissional_id: Optional[int] = None
    metodo: str
    caminho: str
    status_code: Optional[int] = None
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)