from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime
from typing import Optional


class EspecialidadeCreate(BaseModel):
    nome: str


class EspecialidadeResponse(BaseModel):
    id: int
    nome: str

    model_config = ConfigDict(from_attributes=True)


class ProfissionalCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    especialidade_id: Optional[int] = None
    registro_profissional: Optional[str] = None
    nivel_acesso: str = "profissional"  # "profissional" ou "administrador"
    perfil_acesso_id: Optional[int] = None  # só relevante quando nivel_acesso == "profissional"


class ProfissionalUpdate(BaseModel):
    nome: Optional[str] = None
    especialidade_id: Optional[int] = None
    registro_profissional: Optional[str] = None
    nivel_acesso: Optional[str] = None
    perfil_acesso_id: Optional[int] = None
    ativo: Optional[bool] = None


class ProfissionalResponse(BaseModel):
    id: int
    nome: str
    email: EmailStr
    especialidade_id: Optional[int] = None
    registro_profissional: Optional[str] = None
    nivel_acesso: str
    perfil_acesso_id: Optional[int] = None
    ativo: bool
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)