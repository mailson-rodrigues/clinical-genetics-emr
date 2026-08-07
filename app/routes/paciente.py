from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.paciente import Paciente
from app.models.profissional import Profissional
from app.schemas.paciente import PacienteCreate, PacienteUpdate, PacienteResponse
from app.dependencies import exigir_administrador, obter_profissional_opcional

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


@router.post("/", response_model=PacienteResponse, status_code=201)
def criar_paciente(paciente: PacienteCreate, db: Session = Depends(get_db)):
    """Cria um novo paciente."""
    existente = db.query(Paciente).filter(Paciente.documento == paciente.documento).first()
    if existente:
        raise HTTPException(status_code=400, detail="Já existe um paciente com esse documento.")

    novo_paciente = Paciente(**paciente.model_dump())
    db.add(novo_paciente)
    db.commit()
    db.refresh(novo_paciente)
    return novo_paciente


@router.get("/", response_model=List[PacienteResponse])
def listar_pacientes(
    response: Response,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    incluir_inativos: bool = False,
    busca: Optional[str] = None,
    db: Session = Depends(get_db),
    profissional_atual: Optional[Profissional] = Depends(obter_profissional_opcional),
):
    """
    Lista os pacientes cadastrados, paginado (?skip=0&limit=50, limit
    máximo 200), mais recentes primeiro. Por padrão só traz pacientes
    ativos (não removidos); ?incluir_inativos=true também traz os
    removidos (soft delete), restrito a ADMINISTRADOR. Use ?busca=texto
    para filtrar por nome ou documento/CPF (parcial, sem diferenciar
    maiúsculas/minúsculas), combinável com skip/limit. O total de
    registros (considerando esses filtros, mas não a paginação) vai no
    header "X-Total-Count" da resposta.
    """
    query = db.query(Paciente)

    if incluir_inativos:
        if not profissional_atual or profissional_atual.nivel_acesso != "administrador":
            raise HTTPException(
                status_code=403,
                detail="Apenas administradores podem listar pacientes inativos.",
            )
    else:
        query = query.filter(Paciente.ativo.is_(True))

    if busca:
        termo = f"%{busca}%"
        query = query.filter(
            (Paciente.nome.ilike(termo)) | (Paciente.documento.ilike(termo))
        )

    response.headers["X-Total-Count"] = str(query.count())
    return query.order_by(Paciente.criado_em.desc()).offset(skip).limit(limit).all()


@router.get("/{paciente_id}", response_model=PacienteResponse)
def buscar_paciente(paciente_id: int, db: Session = Depends(get_db)):
    """Busca um paciente específico pelo id."""
    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    return paciente


@router.put("/{paciente_id}", response_model=PacienteResponse)
def atualizar_paciente(
    paciente_id: int,
    dados: PacienteUpdate,
    db: Session = Depends(get_db),
    _administrador: Profissional = Depends(exigir_administrador),
):
    """
    Atualiza os dados de um paciente já cadastrado (ex: corrigir nome
    digitado errado). Requer login como ADMINISTRADOR.
    """
    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")

    dados_atualizados = dados.model_dump(exclude_unset=True)
    for campo, valor in dados_atualizados.items():
        setattr(paciente, campo, valor)

    db.commit()
    db.refresh(paciente)
    return paciente


@router.delete("/{paciente_id}", status_code=204)
def remover_paciente(
    paciente_id: int,
    db: Session = Depends(get_db),
    _administrador: Profissional = Depends(exigir_administrador),
):
    """
    Remove um paciente do sistema. Requer login como ADMINISTRADOR.

    Isso é um soft delete: a linha não é apagada de verdade (o registro é
    só marcado como ativo=False), para preservar consultas/histórico
    clínico já vinculados a ele. Pode ser revertido via
    PUT /pacientes/{id} com {"ativo": true}.
    """
    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")

    paciente.ativo = False
    db.commit()
    return None