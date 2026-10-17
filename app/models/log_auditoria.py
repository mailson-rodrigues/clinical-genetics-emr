from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class LogAuditoria(Base):
    """
    Audit record: one row for each relevant action performed in the
    system (who, what, when, result). Generated automatically by
    a middleware - there is no need to call this manually in the routes.
    """
    __tablename__ = "logs_auditoria"

    id = Column(Integer, primary_key=True, index=True)
    profissional_id = Column(Integer, ForeignKey("profissionais.id"), nullable=True)
    metodo = Column(String, nullable=False)       # GET, POST, PUT, DELETE
    caminho = Column(String, nullable=False)       # ex: "/pacientes/3"
    status_code = Column(Integer, nullable=True)    # ex: 200, 404, 403
    criado_em = Column(DateTime(timezone=True), server_default=func.now())