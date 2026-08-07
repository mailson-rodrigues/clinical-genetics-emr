from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.paciente import Paciente
from app.models.profissional import Profissional
from app.models.cid import Cid
from app.models.historico_clinico import (
    Alergia, Doenca, Cirurgia, HistoricoClinico, Operadora, PacienteConvenio
)
from app.schemas.historico_clinico import (
    ItemClinicoCreate,
    ItemClinicoResponse,
    DoencaCreate,
    DoencaResponse,
    OperadoraCreate,
    OperadoraResponse,
    PacienteConvenioCreate,
    PacienteConvenioResponse,
)
from app.dependencies import obter_profissional_atual, exigir_administrador, exigir_acesso_modulo

router = APIRouter(prefix="/pacientes", tags=["Historico Clinico"])
router_operadoras = APIRouter(prefix="/operadoras", tags=["Operadoras (Convenios)"])


def _verificar_paciente(paciente_id: int, db: Session):
    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    return paciente


# =====================================================================
# ALERGIAS (requer login - dado clínico de paciente)
# =====================================================================

@router.post("/{paciente_id}/alergias", response_model=ItemClinicoResponse, status_code=201)
def criar_alergia(
    paciente_id: int,
    item: ItemClinicoCreate,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(exigir_acesso_modulo("historico_clinico")),
):
    _verificar_paciente(paciente_id, db)
    novo = Alergia(paciente_id=paciente_id, descricao=item.descricao)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.get("/{paciente_id}/alergias", response_model=List[ItemClinicoResponse])
def listar_alergias(
    paciente_id: int,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(obter_profissional_atual),
):
    _verificar_paciente(paciente_id, db)
    return db.query(Alergia).filter(Alergia.paciente_id == paciente_id).all()


@router.delete("/{paciente_id}/alergias/{item_id}", status_code=204)
def remover_alergia(
    paciente_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(exigir_acesso_modulo("historico_clinico")),
):
    item = db.query(Alergia).filter(Alergia.id == item_id, Alergia.paciente_id == paciente_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Alergia não encontrada.")
    db.delete(item)
    db.commit()
    return None


# =====================================================================
# DOENÇAS (requer login)
# =====================================================================

@router.post("/{paciente_id}/doencas", response_model=DoencaResponse, status_code=201)
def criar_doenca(
    paciente_id: int,
    item: DoencaCreate,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(exigir_acesso_modulo("historico_clinico")),
):
    _verificar_paciente(paciente_id, db)

    if item.cid_id is not None:
        cid = db.query(Cid).filter(Cid.id == item.cid_id).first()
        if not cid:
            raise HTTPException(status_code=404, detail="Código CID informado não existe no catálogo.")

    novo = Doenca(paciente_id=paciente_id, descricao=item.descricao, cid_id=item.cid_id)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.get("/{paciente_id}/doencas", response_model=List[DoencaResponse])
def listar_doencas(
    paciente_id: int,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(obter_profissional_atual),
):
    _verificar_paciente(paciente_id, db)
    return db.query(Doenca).filter(Doenca.paciente_id == paciente_id).all()


@router.delete("/{paciente_id}/doencas/{item_id}", status_code=204)
def remover_doenca(
    paciente_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(exigir_acesso_modulo("historico_clinico")),
):
    item = db.query(Doenca).filter(Doenca.id == item_id, Doenca.paciente_id == paciente_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Doença não encontrada.")
    db.delete(item)
    db.commit()
    return None


# =====================================================================
# CIRURGIAS (requer login)
# =====================================================================

@router.post("/{paciente_id}/cirurgias", response_model=ItemClinicoResponse, status_code=201)
def criar_cirurgia(
    paciente_id: int,
    item: ItemClinicoCreate,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(exigir_acesso_modulo("historico_clinico")),
):
    _verificar_paciente(paciente_id, db)
    novo = Cirurgia(paciente_id=paciente_id, descricao=item.descricao)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.get("/{paciente_id}/cirurgias", response_model=List[ItemClinicoResponse])
def listar_cirurgias(
    paciente_id: int,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(obter_profissional_atual),
):
    _verificar_paciente(paciente_id, db)
    return db.query(Cirurgia).filter(Cirurgia.paciente_id == paciente_id).all()


@router.delete("/{paciente_id}/cirurgias/{item_id}", status_code=204)
def remover_cirurgia(
    paciente_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(exigir_acesso_modulo("historico_clinico")),
):
    item = db.query(Cirurgia).filter(Cirurgia.id == item_id, Cirurgia.paciente_id == paciente_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cirurgia não encontrada.")
    db.delete(item)
    db.commit()
    return None


# =====================================================================
# HISTÓRICOS CLÍNICOS (requer login)
# =====================================================================

@router.post("/{paciente_id}/historicos", response_model=ItemClinicoResponse, status_code=201)
def criar_historico(
    paciente_id: int,
    item: ItemClinicoCreate,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(exigir_acesso_modulo("historico_clinico")),
):
    _verificar_paciente(paciente_id, db)
    novo = HistoricoClinico(paciente_id=paciente_id, descricao=item.descricao)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.get("/{paciente_id}/historicos", response_model=List[ItemClinicoResponse])
def listar_historicos(
    paciente_id: int,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(obter_profissional_atual),
):
    _verificar_paciente(paciente_id, db)
    return db.query(HistoricoClinico).filter(HistoricoClinico.paciente_id == paciente_id).all()


@router.delete("/{paciente_id}/historicos/{item_id}", status_code=204)
def remover_historico(
    paciente_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(exigir_acesso_modulo("historico_clinico")),
):
    item = db.query(HistoricoClinico).filter(
        HistoricoClinico.id == item_id, HistoricoClinico.paciente_id == paciente_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Registro de histórico não encontrado.")
    db.delete(item)
    db.commit()
    return None


# =====================================================================
# CONVÊNIOS (vínculo paciente <-> operadora) - requer login
# =====================================================================

@router.post("/{paciente_id}/convenios", response_model=PacienteConvenioResponse, status_code=201)
def vincular_convenio(
    paciente_id: int,
    dados: PacienteConvenioCreate,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(exigir_acesso_modulo("historico_clinico")),
):
    _verificar_paciente(paciente_id, db)
    operadora = db.query(Operadora).filter(Operadora.id == dados.operadora_id).first()
    if not operadora:
        raise HTTPException(status_code=404, detail="Operadora não encontrada.")

    novo = PacienteConvenio(
        paciente_id=paciente_id,
        operadora_id=dados.operadora_id,
        numero_carteirinha=dados.numero_carteirinha,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.get("/{paciente_id}/convenios", response_model=List[PacienteConvenioResponse])
def listar_convenios_paciente(
    paciente_id: int,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(obter_profissional_atual),
):
    _verificar_paciente(paciente_id, db)
    return db.query(PacienteConvenio).filter(PacienteConvenio.paciente_id == paciente_id).all()


@router.delete("/{paciente_id}/convenios/{vinculo_id}", status_code=204)
def remover_convenio_paciente(
    paciente_id: int,
    vinculo_id: int,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(exigir_acesso_modulo("historico_clinico")),
):
    item = db.query(PacienteConvenio).filter(
        PacienteConvenio.id == vinculo_id, PacienteConvenio.paciente_id == paciente_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Vínculo de convênio não encontrado.")
    db.delete(item)
    db.commit()
    return None


# =====================================================================
# OPERADORAS (catálogo) - listagem aberta, criação exige ADMINISTRADOR
# =====================================================================

@router_operadoras.post("/", response_model=OperadoraResponse, status_code=201)
def criar_operadora(
    dados: OperadoraCreate,
    db: Session = Depends(get_db),
    _administrador: Profissional = Depends(exigir_administrador),
):
    existente = db.query(Operadora).filter(Operadora.nome == dados.nome).first()
    if existente:
        raise HTTPException(status_code=400, detail="Operadora já cadastrada.")
    nova = Operadora(nome=dados.nome)
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova


@router_operadoras.get("/", response_model=List[OperadoraResponse])
def listar_operadoras(db: Session = Depends(get_db)):
    return db.query(Operadora).all()