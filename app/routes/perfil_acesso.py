from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.perfil_acesso import Modulo, PerfilAcesso, PerfilAcessoModulo
from app.models.profissional import Profissional
from app.schemas.perfil_acesso import (
    ModuloResponse,
    PerfilAcessoCreate,
    PerfilAcessoUpdate,
    PerfilAcessoResponse,
    VincularModuloRequest,
)
from app.dependencies import exigir_administrador

router_modulos = APIRouter(prefix="/modulos", tags=["Modulos"])
router = APIRouter(prefix="/perfis-acesso", tags=["Perfis de Acesso"])


def _serializar_perfil(db: Session, perfil: PerfilAcesso) -> PerfilAcessoResponse:
    modulos = (
        db.query(Modulo)
        .join(PerfilAcessoModulo, PerfilAcessoModulo.modulo_id == Modulo.id)
        .filter(PerfilAcessoModulo.perfil_acesso_id == perfil.id)
        .order_by(Modulo.nome)
        .all()
    )
    return PerfilAcessoResponse(
        id=perfil.id,
        nome=perfil.nome,
        descricao=perfil.descricao,
        modulos=[ModuloResponse.model_validate(modulo) for modulo in modulos],
    )


# =====================================================================
# MÓDULOS (catálogo fixo do sistema, só leitura)
# =====================================================================

@router_modulos.get("/", response_model=List[ModuloResponse])
def listar_modulos(
    db: Session = Depends(get_db),
    _administrador: Profissional = Depends(exigir_administrador),
):
    """Lista o catálogo fixo de módulos do sistema. Requer login como ADMINISTRADOR."""
    return db.query(Modulo).order_by(Modulo.nome).all()


# =====================================================================
# PERFIS DE ACESSO
# =====================================================================

@router.post("/", response_model=PerfilAcessoResponse, status_code=201)
def criar_perfil_acesso(
    dados: PerfilAcessoCreate,
    db: Session = Depends(get_db),
    _administrador: Profissional = Depends(exigir_administrador),
):
    """Cria um novo perfil de acesso. Requer login como ADMINISTRADOR."""
    existente = db.query(PerfilAcesso).filter(PerfilAcesso.nome == dados.nome).first()
    if existente:
        raise HTTPException(status_code=400, detail="Já existe um perfil de acesso com esse nome.")

    novo = PerfilAcesso(nome=dados.nome, descricao=dados.descricao)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return _serializar_perfil(db, novo)


@router.get("/", response_model=List[PerfilAcessoResponse])
def listar_perfis_acesso(
    db: Session = Depends(get_db),
    _administrador: Profissional = Depends(exigir_administrador),
):
    """Lista os perfis de acesso cadastrados, cada um já com seus módulos vinculados."""
    perfis = db.query(PerfilAcesso).order_by(PerfilAcesso.nome).all()
    return [_serializar_perfil(db, perfil) for perfil in perfis]


@router.get("/{perfil_id}", response_model=PerfilAcessoResponse)
def buscar_perfil_acesso(
    perfil_id: int,
    db: Session = Depends(get_db),
    _administrador: Profissional = Depends(exigir_administrador),
):
    perfil = db.query(PerfilAcesso).filter(PerfilAcesso.id == perfil_id).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil de acesso não encontrado.")
    return _serializar_perfil(db, perfil)


@router.put("/{perfil_id}", response_model=PerfilAcessoResponse)
def atualizar_perfil_acesso(
    perfil_id: int,
    dados: PerfilAcessoUpdate,
    db: Session = Depends(get_db),
    _administrador: Profissional = Depends(exigir_administrador),
):
    perfil = db.query(PerfilAcesso).filter(PerfilAcesso.id == perfil_id).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil de acesso não encontrado.")

    dados_atualizados = dados.model_dump(exclude_unset=True)

    if "nome" in dados_atualizados:
        existente = db.query(PerfilAcesso).filter(
            PerfilAcesso.nome == dados_atualizados["nome"],
            PerfilAcesso.id != perfil_id,
        ).first()
        if existente:
            raise HTTPException(status_code=400, detail="Já existe um perfil de acesso com esse nome.")

    for campo, valor in dados_atualizados.items():
        setattr(perfil, campo, valor)

    db.commit()
    db.refresh(perfil)
    return _serializar_perfil(db, perfil)


@router.delete("/{perfil_id}", status_code=204)
def remover_perfil_acesso(
    perfil_id: int,
    db: Session = Depends(get_db),
    _administrador: Profissional = Depends(exigir_administrador),
):
    """Remove um perfil de acesso. Bloqueado se algum profissional ainda estiver vinculado a ele."""
    perfil = db.query(PerfilAcesso).filter(PerfilAcesso.id == perfil_id).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil de acesso não encontrado.")

    profissional_vinculado = db.query(Profissional).filter(Profissional.perfil_acesso_id == perfil_id).first()
    if profissional_vinculado:
        raise HTTPException(
            status_code=400,
            detail="Não é possível remover: há profissionais vinculados a este perfil de acesso.",
        )

    db.query(PerfilAcessoModulo).filter(PerfilAcessoModulo.perfil_acesso_id == perfil_id).delete()
    db.delete(perfil)
    db.commit()
    return None


@router.post("/{perfil_id}/modulos", response_model=PerfilAcessoResponse, status_code=201)
def vincular_modulo(
    perfil_id: int,
    dados: VincularModuloRequest,
    db: Session = Depends(get_db),
    _administrador: Profissional = Depends(exigir_administrador),
):
    perfil = db.query(PerfilAcesso).filter(PerfilAcesso.id == perfil_id).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil de acesso não encontrado.")

    modulo = db.query(Modulo).filter(Modulo.id == dados.modulo_id).first()
    if not modulo:
        raise HTTPException(status_code=404, detail="Módulo informado não existe.")

    ja_vinculado = db.query(PerfilAcessoModulo).filter(
        PerfilAcessoModulo.perfil_acesso_id == perfil_id,
        PerfilAcessoModulo.modulo_id == dados.modulo_id,
    ).first()
    if not ja_vinculado:
        db.add(PerfilAcessoModulo(perfil_acesso_id=perfil_id, modulo_id=dados.modulo_id))
        db.commit()

    return _serializar_perfil(db, perfil)


@router.delete("/{perfil_id}/modulos/{modulo_id}", status_code=204)
def desvincular_modulo(
    perfil_id: int,
    modulo_id: int,
    db: Session = Depends(get_db),
    _administrador: Profissional = Depends(exigir_administrador),
):
    perfil = db.query(PerfilAcesso).filter(PerfilAcesso.id == perfil_id).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil de acesso não encontrado.")

    vinculo = db.query(PerfilAcessoModulo).filter(
        PerfilAcessoModulo.perfil_acesso_id == perfil_id,
        PerfilAcessoModulo.modulo_id == modulo_id,
    ).first()
    if not vinculo:
        raise HTTPException(status_code=404, detail="Este módulo não está vinculado a esse perfil.")

    db.delete(vinculo)
    db.commit()
    return None
