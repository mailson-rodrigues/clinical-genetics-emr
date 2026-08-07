from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import date, datetime
from typing import Optional


class PacienteBase(BaseModel):
    # Dados pessoais
    nome: str
    nome_social: Optional[str] = None
    data_nascimento: date
    sexo: str
    tipo_sanguineo: Optional[str] = None
    documento: str
    rg: Optional[str] = None
    foto_base64: Optional[str] = None

    # Contato
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[EmailStr] = None

    # Endereço
    cep: Optional[str] = None
    endereco: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None

    # Recém-nascido / responsável
    recem_nascido: bool = False
    nome_responsavel: Optional[str] = None
    parentesco_responsavel: Optional[str] = None

    # Preferências
    aceita_mensagens: bool = True

    # LGPD
    autorizacao_lgpd: bool = False
    data_autorizacao_lgpd: Optional[datetime] = None
    documento_autorizacao_lgpd: Optional[str] = None


class PacienteCreate(PacienteBase):
    pass


class PacienteUpdate(BaseModel):
    nome: Optional[str] = None
    nome_social: Optional[str] = None
    data_nascimento: Optional[date] = None
    sexo: Optional[str] = None
    tipo_sanguineo: Optional[str] = None
    rg: Optional[str] = None
    foto_base64: Optional[str] = None
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[EmailStr] = None
    cep: Optional[str] = None
    endereco: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    recem_nascido: Optional[bool] = None
    nome_responsavel: Optional[str] = None
    parentesco_responsavel: Optional[str] = None
    aceita_mensagens: Optional[bool] = None
    autorizacao_lgpd: Optional[bool] = None
    data_autorizacao_lgpd: Optional[datetime] = None
    documento_autorizacao_lgpd: Optional[str] = None
    ativo: Optional[bool] = None  # permite reativar um paciente removido (soft delete)


class PacienteResponse(PacienteBase):
    id: int
    ativo: bool
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
        