from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.anamnese import Pergunta
from app.schemas.anamnese import PerguntaResponse

router = APIRouter(prefix="/perguntas", tags=["Perguntas (roteiro)"])


@router.get("/", response_model=List[PerguntaResponse])
def listar_perguntas(db: Session = Depends(get_db)):
    """Lista o roteiro completo de perguntas, em ordem."""
    return db.query(Pergunta).order_by(Pergunta.ordem).all()