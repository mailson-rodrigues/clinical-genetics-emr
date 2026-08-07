from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class LogAuditoria(Base):
    """
    Registro de auditoria: uma linha para cada ação relevante feita no
    sistema (quem, o quê, quando, resultado). Gerado automaticamente por
    um middleware - não é necessário chamar isso manualmente nas rotas.
    """
    __tablename__ = "logs_auditoria"

    id = Column(Integer, primary_key=True, index=True)
    profissional_id = Column(Integer, ForeignKey("profissionais.id"), nullable=True)
    metodo = Column(String, nullable=False)       # GET, POST, PUT, DELETE
    caminho = Column(String, nullable=False)       # ex: "/pacientes/3"
    status_code = Column(Integer, nullable=True)    # ex: 200, 404, 403
    criado_em = Column(DateTime(timezone=True), server_default=func.now())