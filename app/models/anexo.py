from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Anexo(Base):
    """
    File (document, PDF report, exam image) linked to a
    Paciente OR an Exame - never both, never neither (validated in the
    creation route, not in the database). The file itself stays on disk, in
    uploads/ (outside frontend/, so it is not reachable without
    authentication through the static mount) - only the metadata lives here.
    """
    __tablename__ = "anexos"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=True)
    exame_id = Column(Integer, ForeignKey("exames.id"), nullable=True)
    profissional_id = Column(Integer, ForeignKey("profissionais.id"), nullable=True)  # quem enviou

    nome_original = Column(String, nullable=False)  # file name, to show to the user
    nome_armazenado = Column(String, nullable=False)  # uuid4 + extension, the real name on disk
    tipo_conteudo = Column(String, nullable=False)  # ex: "application/pdf"
    tamanho_bytes = Column(Integer, nullable=False)

    criado_em = Column(DateTime(timezone=True), server_default=func.now())
