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
    """Creates a new patient."""
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
    Lists the registered patients, paginated (?skip=0&limit=50, maximum
    limit 200), most recent first. By default only returns active patients
    (not removed); ?incluir_inativos=true also returns the
    removed ones (soft delete), restricted to ADMINISTRATOR. Use ?busca=text
    to filter by name or document/CPF (partial, case-insensitive),
    combinable with skip/limit. The total number of
    records (considering these filters, but not the pagination) goes in the
    "X-Total-Count" response header.
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
    """Fetches a specific patient by id."""
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
    Updates the data of an already registered patient (e.g. fixing a
    misspelled name). Requires login as ADMINISTRATOR.
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
    Removes a patient from the system. Requires login as ADMINISTRATOR.

    This is a soft delete: the row is not really deleted (the record is
    only marked as ativo=False), to preserve the consultations/clinical
    history already linked to it. It can be reverted via
    PUT /pacientes/{id} with {"ativo": true}.
    """
    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")

    paciente.ativo = False
    db.commit()
    return None