from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.perfil_acesso import PerfilAcesso
from app.models.profissional import Profissional, Especialidade
from app.schemas.profissional import (
    ProfissionalCreate,
    ProfissionalUpdate,
    ProfissionalResponse,
    EspecialidadeCreate,
    EspecialidadeResponse,
)
from app.services.seguranca import gerar_hash_senha
from app.dependencies import exigir_administrador

router = APIRouter(prefix="/profissionais", tags=["Profissionais"])
router_especialidades = APIRouter(prefix="/especialidades", tags=["Especialidades"])


# =====================================================================
# ESPECIALIDADES (catálogo)
# =====================================================================

@router_especialidades.post("/", response_model=EspecialidadeResponse, status_code=201)
def criar_especialidade(dados: EspecialidadeCreate, db: Session = Depends(get_db)):
    existente = db.query(Especialidade).filter(Especialidade.nome == dados.nome).first()
    if existente:
        raise HTTPException(status_code=400, detail="Esta especialidade já está cadastrada.")

    nova = Especialidade(nome=dados.nome)
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova


@router_especialidades.get("/", response_model=List[EspecialidadeResponse])
def listar_especialidades(db: Session = Depends(get_db)):
    return db.query(Especialidade).order_by(Especialidade.nome).all()


# =====================================================================
# PROFISSIONAIS
# =====================================================================

@router.post("/", response_model=ProfissionalResponse, status_code=201)
def criar_profissional(dados: ProfissionalCreate, db: Session = Depends(get_db)):
    """
    Cadastra um novo profissional. A senha é convertida em hash antes de
    salvar. Nota: a criação NÃO exige login, para permitir o cadastro do
    primeiro administrador do sistema. Em produção real, considere
    restringir esta rota depois que já existir ao menos um administrador.
    """
    existente = db.query(Profissional).filter(Profissional.email == dados.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="Já existe um profissional com este e-mail.")

    if dados.especialidade_id is not None:
        especialidade = db.query(Especialidade).filter(Especialidade.id == dados.especialidade_id).first()
        if not especialidade:
            raise HTTPException(status_code=404, detail="Especialidade informada não existe.")

    if dados.nivel_acesso not in ("profissional", "administrador"):
        raise HTTPException(status_code=400, detail="nivel_acesso deve ser 'profissional' ou 'administrador'.")

    if dados.perfil_acesso_id is not None:
        perfil = db.query(PerfilAcesso).filter(PerfilAcesso.id == dados.perfil_acesso_id).first()
        if not perfil:
            raise HTTPException(status_code=404, detail="Perfil de acesso informado não existe.")

    novo_profissional = Profissional(
        nome=dados.nome,
        email=dados.email,
        senha_hash=gerar_hash_senha(dados.senha),
        especialidade_id=dados.especialidade_id,
        registro_profissional=dados.registro_profissional,
        nivel_acesso=dados.nivel_acesso,
        perfil_acesso_id=dados.perfil_acesso_id,
    )
    db.add(novo_profissional)
    db.commit()
    db.refresh(novo_profissional)
    return novo_profissional


@router.get("/", response_model=List[ProfissionalResponse])
def listar_profissionais(db: Session = Depends(get_db)):
    return db.query(Profissional).all()


@router.get("/{profissional_id}", response_model=ProfissionalResponse)
def buscar_profissional(profissional_id: int, db: Session = Depends(get_db)):
    profissional = db.query(Profissional).filter(Profissional.id == profissional_id).first()
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado.")
    return profissional


@router.put("/{profissional_id}", response_model=ProfissionalResponse)
def atualizar_profissional(
    profissional_id: int,
    dados: ProfissionalUpdate,
    db: Session = Depends(get_db),
    _administrador: Profissional = Depends(exigir_administrador),
):
    """
    Atualiza dados de um profissional (especialidade, registro, nível de
    acesso, ativo/inativo). Requer login como ADMINISTRADOR.
    """
    profissional = db.query(Profissional).filter(Profissional.id == profissional_id).first()
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado.")

    dados_atualizados = dados.model_dump(exclude_unset=True)

    if "nivel_acesso" in dados_atualizados and dados_atualizados["nivel_acesso"] not in ("profissional", "administrador"):
        raise HTTPException(status_code=400, detail="nivel_acesso deve ser 'profissional' ou 'administrador'.")

    if dados_atualizados.get("perfil_acesso_id") is not None:
        perfil = db.query(PerfilAcesso).filter(PerfilAcesso.id == dados_atualizados["perfil_acesso_id"]).first()
        if not perfil:
            raise HTTPException(status_code=404, detail="Perfil de acesso informado não existe.")

    for campo, valor in dados_atualizados.items():
        setattr(profissional, campo, valor)

    db.commit()
    db.refresh(profissional)
    return profissional