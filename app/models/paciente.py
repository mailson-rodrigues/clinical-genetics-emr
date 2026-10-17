from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, Text, true
from sqlalchemy.sql import func
from app.database import Base


class Paciente(Base):
    """
    Represents the 'pacientes' table in the database.
    """
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)

    # ---- Personal data ----
    nome = Column(String, nullable=False)
    nome_social = Column(String, nullable=True)
    data_nascimento = Column(Date, nullable=False)
    sexo = Column(String, nullable=False)  # "M", "F" or "Outro"
    tipo_sanguineo = Column(String, nullable=True)  # ex: "A+", "O-"
    documento = Column(String, unique=True, index=True, nullable=False)  # CPF
    rg = Column(String, nullable=True)
    foto_base64 = Column(Text, nullable=True)  # patient photo, base64-encoded

    # ---- Contato ----
    telefone = Column(String, nullable=True)
    whatsapp = Column(String, nullable=True)
    email = Column(String, nullable=True)

    # ---- Address ----
    cep = Column(String, nullable=True)
    endereco = Column(String, nullable=True)
    numero = Column(String, nullable=True)
    complemento = Column(String, nullable=True)
    bairro = Column(String, nullable=True)
    cidade = Column(String, nullable=True)
    uf = Column(String, nullable=True)

    # ---- Newborn / legal guardian ----
    recem_nascido = Column(Boolean, default=False)
    nome_responsavel = Column(String, nullable=True)
    parentesco_responsavel = Column(String, nullable=True)

    # ---- Preferences ----
    aceita_mensagens = Column(Boolean, default=True)

    # ---- LGPD ----
    autorizacao_lgpd = Column(Boolean, default=False)
    data_autorizacao_lgpd = Column(DateTime(timezone=True), nullable=True)
    documento_autorizacao_lgpd = Column(String, nullable=True)  # file path/name

    # Soft delete: when "removing" a patient, we only mark ativo=False instead
    # of deleting the row - this preserves the linked clinical history/
    # consultations and allows the removal to be reverted.
    ativo = Column(Boolean, nullable=False, default=True, server_default=true())

    criado_em = Column(DateTime(timezone=True), server_default=func.now())