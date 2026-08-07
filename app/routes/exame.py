from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.anamnese import Consulta
from app.models.exame import Exame
from app.models.heredograma import Individuo
from app.models.profissional import Profissional
from app.schemas.exame import ExameCreate, ExameUpdate, ExameResponse
from app.dependencies import exigir_acesso_modulo

router = APIRouter(prefix="/consultas", tags=["Exames"])

STATUS_VALIDOS = ("solicitado", "em_andamento", "concluido", "cancelado")


def _validar_individuo_da_consulta(db: Session, individuo_id: int, consulta_id: int):
    individuo = db.query(Individuo).filter(
        Individuo.id == individuo_id,
        Individuo.consulta_id == consulta_id,
    ).first()
    if not individuo:
        raise HTTPException(status_code=404, detail="Indivíduo informado não pertence a essa consulta.")


@router.post("/{consulta_id}/exames", response_model=ExameResponse, status_code=201)
def criar_exame(
    consulta_id: int,
    dados: ExameCreate,
    db: Session = Depends(get_db),
    profissional_atual: Profissional = Depends(exigir_acesso_modulo("exames")),
):
    """Registra a solicitação de um exame para a consulta. Requer login."""
    consulta = db.query(Consulta).filter(Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")

    if dados.individuo_id is not None:
        _validar_individuo_da_consulta(db, dados.individuo_id, consulta_id)

    if dados.status is not None and dados.status not in STATUS_VALIDOS:
        raise HTTPException(status_code=400, detail=f"status deve ser um de: {', '.join(STATUS_VALIDOS)}.")

    novo = Exame(
        consulta_id=consulta_id,
        individuo_id=dados.individuo_id,
        profissional_id=profissional_atual.id,
        tipo_exame=dados.tipo_exame,
        status=dados.status or "solicitado",
        data_solicitacao=dados.data_solicitacao,
        resultado=dados.resultado,
        observacoes=dados.observacoes,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.get("/{consulta_id}/exames", response_model=List[ExameResponse])
def listar_exames(consulta_id: int, db: Session = Depends(get_db)):
    """Lista os exames registrados para uma consulta."""
    consulta = db.query(Consulta).filter(Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")

    return db.query(Exame).filter(Exame.consulta_id == consulta_id).all()


@router.put("/{consulta_id}/exames/{exame_id}", response_model=ExameResponse)
def atualizar_exame(
    consulta_id: int,
    exame_id: int,
    dados: ExameUpdate,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(exigir_acesso_modulo("exames")),
):
    """Atualiza um exame (ex: registrar resultado, mudar status). Requer login."""
    exame = db.query(Exame).filter(
        Exame.id == exame_id,
        Exame.consulta_id == consulta_id,
    ).first()
    if not exame:
        raise HTTPException(status_code=404, detail="Exame não encontrado nessa consulta.")

    if dados.individuo_id is not None:
        _validar_individuo_da_consulta(db, dados.individuo_id, consulta_id)

    if dados.status is not None and dados.status not in STATUS_VALIDOS:
        raise HTTPException(status_code=400, detail=f"status deve ser um de: {', '.join(STATUS_VALIDOS)}.")

    dados_atualizados = dados.model_dump(exclude_unset=True)
    for campo, valor in dados_atualizados.items():
        setattr(exame, campo, valor)

    db.commit()
    db.refresh(exame)
    return exame


@router.delete("/{consulta_id}/exames/{exame_id}", status_code=204)
def remover_exame(
    consulta_id: int,
    exame_id: int,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(exigir_acesso_modulo("exames")),
):
    """Remove um exame. Requer login."""
    exame = db.query(Exame).filter(
        Exame.id == exame_id,
        Exame.consulta_id == consulta_id,
    ).first()
    if not exame:
        raise HTTPException(status_code=404, detail="Exame não encontrado nessa consulta.")

    db.delete(exame)
    db.commit()
    return None
