from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.anamnese import Consulta, Resposta, Pergunta
from app.models.paciente import Paciente
from app.models.profissional import Profissional
from app.dependencies import exigir_acesso_modulo
from app.rate_limit import limiter
from app.schemas.anamnese import (
    ConsultaCreate,
    ConsultaUpdate,
    ConsultaResponse,
    ConsultaComRespostas,
    RespostaCreate,
    RespostaUpdate,
    RespostaResponse,
)
from app.models.heredograma import Individuo, Relacionamento
from app.schemas.heredograma import HeredogramaResponse
from app.services.ia_extracao import extrair_heredograma

router = APIRouter(prefix="/consultas", tags=["Consultas"])


@router.post("/", response_model=ConsultaResponse, status_code=201)
def criar_consulta(
    consulta: ConsultaCreate,
    db: Session = Depends(get_db),
    profissional_atual: Profissional = Depends(exigir_acesso_modulo("consultas")),
):
    """Starts a new consultation/anamnesis for an already registered patient. Requires login."""
    paciente = db.query(Paciente).filter(Paciente.id == consulta.paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")

    nova_consulta = Consulta(
        paciente_id=consulta.paciente_id,
        condicao_investigada=consulta.condicao_investigada,
        profissional_id=profissional_atual.id,
    )
    db.add(nova_consulta)
    db.commit()
    db.refresh(nova_consulta)
    return nova_consulta


@router.get("/", response_model=List[ConsultaResponse])
def listar_consultas(
    response: Response,
    paciente_id: Optional[int] = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """
    Lists consultations, paginated (?skip=0&limit=50, maximum limit 200).
    Optionally filters by patient (?paciente_id=1). The total number of
    records (already considering the filter, but not the pagination) goes in the
    "X-Total-Count" response header.
    """
    query = db.query(Consulta)
    if paciente_id is not None:
        query = query.filter(Consulta.paciente_id == paciente_id)

    response.headers["X-Total-Count"] = str(query.count())
    return query.offset(skip).limit(limit).all()


@router.get("/{consulta_id}", response_model=ConsultaComRespostas)
def buscar_consulta(consulta_id: int, db: Session = Depends(get_db)):
    """Fetches a specific consultation, already with all the recorded answers."""
    consulta = db.query(Consulta).filter(Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")
    return consulta


@router.put("/{consulta_id}", response_model=ConsultaResponse)
def atualizar_consulta(consulta_id: int, dados: ConsultaUpdate, db: Session = Depends(get_db)):
    """Updates consultation data (e.g. mark it as completed)."""
    consulta = db.query(Consulta).filter(Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")

    dados_atualizados = dados.model_dump(exclude_unset=True)
    for campo, valor in dados_atualizados.items():
        setattr(consulta, campo, valor)

    db.commit()
    db.refresh(consulta)
    return consulta


@router.post("/{consulta_id}/respostas", response_model=RespostaResponse, status_code=201)
def registrar_resposta(
    consulta_id: int,
    resposta: RespostaCreate,
    db: Session = Depends(get_db),
    profissional_atual: Profissional = Depends(exigir_acesso_modulo("consultas")),
):
    """Records the answer to a question of the script, within a consultation. Requires login."""
    consulta = db.query(Consulta).filter(Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")

    pergunta = db.query(Pergunta).filter(Pergunta.id == resposta.pergunta_id).first()
    if not pergunta:
        raise HTTPException(status_code=404, detail="Pergunta não encontrada.")

    nova_resposta = Resposta(
        consulta_id=consulta_id,
        pergunta_id=resposta.pergunta_id,
        resposta_texto=resposta.resposta_texto,
    )
    db.add(nova_resposta)
    db.commit()
    db.refresh(nova_resposta)
    return nova_resposta


@router.put("/{consulta_id}/respostas/{resposta_id}", response_model=RespostaResponse)
def atualizar_resposta(
    consulta_id: int,
    resposta_id: int,
    dados: RespostaUpdate,
    db: Session = Depends(get_db),
    profissional_atual: Profissional = Depends(exigir_acesso_modulo("consultas")),
):
    """Updates the text of an answer already recorded in this consultation. Requires login."""
    resposta = db.query(Resposta).filter(
        Resposta.id == resposta_id,
        Resposta.consulta_id == consulta_id,
    ).first()
    if not resposta:
        raise HTTPException(status_code=404, detail="Resposta não encontrada nessa consulta.")

    resposta.resposta_texto = dados.resposta_texto
    db.commit()
    db.refresh(resposta)
    return resposta


@router.get("/{consulta_id}/respostas", response_model=List[RespostaResponse])
def listar_respostas(consulta_id: int, db: Session = Depends(get_db)):
    """Lists all the answers already recorded for a consultation."""
    consulta = db.query(Consulta).filter(Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")

    return db.query(Resposta).filter(Resposta.consulta_id == consulta_id).all()


@router.post("/{consulta_id}/gerar-heredograma", response_model=HeredogramaResponse)
@limiter.limit("60/minute")
def gerar_heredograma(
    request: Request,
    consulta_id: int,
    db: Session = Depends(get_db),
    profissional_atual: Profissional = Depends(exigir_acesso_modulo("consultas")),
):
    """
    Uses AI to analyze all the answers recorded in the consultation
    and generate (or regenerate) the individuals and relationships of the pedigree.
    Requires login.

    Limited to 60 requests/minute per IP (@limiter.limit) - it is the route
    that consumes the paid Anthropic API, so it is the most important one to
    protect against abuse. Once the limit is exceeded, responds 429 Too Many Requests.
    """
    consulta = db.query(Consulta).filter(Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")

    respostas = db.query(Resposta).filter(Resposta.consulta_id == consulta_id).all()
    if not respostas:
        raise HTTPException(
            status_code=400,
            detail="Essa consulta ainda não tem respostas registradas."
        )

    perguntas_e_respostas = []
    for resposta in respostas:
        perguntas_e_respostas.append({
            "categoria": resposta.pergunta.categoria,
            "pergunta": resposta.pergunta.texto,
            "resposta": resposta.resposta_texto,
        })

    try:
        heredograma_extraido = extrair_heredograma(
            condicao_investigada=consulta.condicao_investigada,
            perguntas_e_respostas=perguntas_e_respostas,
        )
    except ValueError as erro:
        raise HTTPException(status_code=502, detail=str(erro))

    db.query(Individuo).filter(Individuo.consulta_id == consulta_id).delete()
    db.query(Relacionamento).filter(Relacionamento.consulta_id == consulta_id).delete()

    for individuo_extraido in heredograma_extraido.individuos:
        novo_individuo = Individuo(
            consulta_id=consulta_id,
            **individuo_extraido.model_dump()
        )
        db.add(novo_individuo)

    for relacionamento_extraido in heredograma_extraido.relacionamentos:
        novo_relacionamento = Relacionamento(
            consulta_id=consulta_id,
            **relacionamento_extraido.model_dump()
        )
        db.add(novo_relacionamento)

    db.commit()

    individuos_salvos = db.query(Individuo).filter(Individuo.consulta_id == consulta_id).all()
    relacionamentos_salvos = db.query(Relacionamento).filter(Relacionamento.consulta_id == consulta_id).all()

    return HeredogramaResponse(
        consulta_id=consulta_id,
        individuos=individuos_salvos,
        relacionamentos=relacionamentos_salvos,
    )


@router.get("/{consulta_id}/heredograma", response_model=HeredogramaResponse)
def buscar_heredograma(consulta_id: int, db: Session = Depends(get_db)):
    """Returns the already generated pedigree (without calling the AI again)."""
    consulta = db.query(Consulta).filter(Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")

    individuos = db.query(Individuo).filter(Individuo.consulta_id == consulta_id).all()
    relacionamentos = db.query(Relacionamento).filter(Relacionamento.consulta_id == consulta_id).all()

    if not individuos:
        raise HTTPException(
            status_code=404,
            detail="Heredograma ainda não foi gerado para essa consulta."
        )

    return HeredogramaResponse(
        consulta_id=consulta_id,
        individuos=individuos,
        relacionamentos=relacionamentos,
    )