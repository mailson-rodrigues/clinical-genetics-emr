from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.cid import Cid
from app.models.profissional import Profissional
from app.schemas.cid import CidCreate, CidResponse
from app.dependencies import exigir_administrador

router = APIRouter(prefix="/cids", tags=["CID (Classificacao Internacional de Doencas)"])


@router.post("/", response_model=CidResponse, status_code=201)
def criar_cid(
    dados: CidCreate,
    db: Session = Depends(get_db),
    _administrador: Profissional = Depends(exigir_administrador),
):
    """Cadastra um novo código CID no catálogo. Requer login como ADMINISTRADOR."""
    existente = db.query(Cid).filter(Cid.codigo == dados.codigo).first()
    if existente:
        raise HTTPException(status_code=400, detail="Este código CID já está cadastrado.")

    novo = Cid(**dados.model_dump())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.get("/", response_model=List[CidResponse])
def listar_cids(busca: Optional[str] = None, versao: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Lista os códigos CID cadastrados. Use ?busca=texto para filtrar por
    código ou descrição (ex: ?busca=mama ou ?busca=C50), e/ou
    ?versao=CID-10 (ou CID-11, quando existir) para filtrar pela versão.
    """
    query = db.query(Cid)
    if busca:
        termo = f"%{busca}%"
        query = query.filter(
            (Cid.codigo.ilike(termo)) | (Cid.descricao.ilike(termo))
        )
    if versao:
        query = query.filter(Cid.versao == versao)
    return query.order_by(Cid.codigo).all()


@router.get("/{cid_id}", response_model=CidResponse)
def buscar_cid(cid_id: int, db: Session = Depends(get_db)):
    cid = db.query(Cid).filter(Cid.id == cid_id).first()
    if not cid:
        raise HTTPException(status_code=404, detail="Código CID não encontrado.")
    return cid