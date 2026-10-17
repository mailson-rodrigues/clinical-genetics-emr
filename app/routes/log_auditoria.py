from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.log_auditoria import LogAuditoria
from app.models.profissional import Profissional
from app.schemas.log_auditoria import LogAuditoriaResponse
from app.dependencies import exigir_administrador

router = APIRouter(prefix="/logs", tags=["Logs de Auditoria"])


@router.get("/", response_model=List[LogAuditoriaResponse])
def listar_logs(
    profissional_id: Optional[int] = None,
    limite: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _administrador: Profissional = Depends(exigir_administrador),
):
    """
    Lists the audit records, most recent first. Requires login
    as ADMINISTRATOR. Optional filter by professional (?profissional_id=1)
    and result limit (?limite=50, maximum 500).
    """
    query = db.query(LogAuditoria).order_by(LogAuditoria.id.desc())
    if profissional_id is not None:
        query = query.filter(LogAuditoria.profissional_id == profissional_id)
    return query.limit(limite).all()