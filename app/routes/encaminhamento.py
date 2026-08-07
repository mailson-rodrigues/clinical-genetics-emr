from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.anamnese import Consulta
from app.models.encaminhamento import Encaminhamento
from app.models.profissional import Especialidade, Profissional
from app.schemas.encaminhamento import (
    EncaminhamentoCreate,
    EncaminhamentoUpdate,
    EncaminhamentoResponse,
)
from app.dependencies import exigir_acesso_modulo

router = APIRouter(prefix="/consultas", tags=["Encaminhamentos"])


@router.post("/{consulta_id}/encaminhamentos", response_model=EncaminhamentoResponse, status_code=201)
def criar_encaminhamento(
    consulta_id: int,
    dados: EncaminhamentoCreate,
    db: Session = Depends(get_db),
    profissional_atual: Profissional = Depends(exigir_acesso_modulo("encaminhamentos")),
):
    """Registra um encaminhamento para outro especialista. Requer login."""
    consulta = db.query(Consulta).filter(Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")

    if dados.especialidade_id is not None:
        especialidade = db.query(Especialidade).filter(Especialidade.id == dados.especialidade_id).first()
        if not especialidade:
            raise HTTPException(status_code=404, detail="Especialidade informada não existe.")

    novo = Encaminhamento(
        consulta_id=consulta_id,
        especialidade_id=dados.especialidade_id,
        profissional_id=profissional_atual.id,
        motivo=dados.motivo,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.get("/{consulta_id}/encaminhamentos", response_model=List[EncaminhamentoResponse])
def listar_encaminhamentos(consulta_id: int, db: Session = Depends(get_db)):
    """Lista os encaminhamentos registrados para uma consulta."""
    consulta = db.query(Consulta).filter(Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")

    return db.query(Encaminhamento).filter(Encaminhamento.consulta_id == consulta_id).all()


@router.put("/{consulta_id}/encaminhamentos/{encaminhamento_id}", response_model=EncaminhamentoResponse)
def atualizar_encaminhamento(
    consulta_id: int,
    encaminhamento_id: int,
    dados: EncaminhamentoUpdate,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(exigir_acesso_modulo("encaminhamentos")),
):
    """Atualiza um encaminhamento (ex: marcar como concluído). Requer login."""
    encaminhamento = db.query(Encaminhamento).filter(
        Encaminhamento.id == encaminhamento_id,
        Encaminhamento.consulta_id == consulta_id,
    ).first()
    if not encaminhamento:
        raise HTTPException(status_code=404, detail="Encaminhamento não encontrado nessa consulta.")

    if dados.especialidade_id is not None:
        especialidade = db.query(Especialidade).filter(Especialidade.id == dados.especialidade_id).first()
        if not especialidade:
            raise HTTPException(status_code=404, detail="Especialidade informada não existe.")

    if dados.status is not None and dados.status not in ("pendente", "concluido", "cancelado"):
        raise HTTPException(status_code=400, detail="status deve ser 'pendente', 'concluido' ou 'cancelado'.")

    dados_atualizados = dados.model_dump(exclude_unset=True)
    for campo, valor in dados_atualizados.items():
        setattr(encaminhamento, campo, valor)

    db.commit()
    db.refresh(encaminhamento)
    return encaminhamento


@router.delete("/{consulta_id}/encaminhamentos/{encaminhamento_id}", status_code=204)
def remover_encaminhamento(
    consulta_id: int,
    encaminhamento_id: int,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(exigir_acesso_modulo("encaminhamentos")),
):
    """Remove um encaminhamento. Requer login."""
    encaminhamento = db.query(Encaminhamento).filter(
        Encaminhamento.id == encaminhamento_id,
        Encaminhamento.consulta_id == consulta_id,
    ).first()
    if not encaminhamento:
        raise HTTPException(status_code=404, detail="Encaminhamento não encontrado nessa consulta.")

    db.delete(encaminhamento)
    db.commit()
    return None