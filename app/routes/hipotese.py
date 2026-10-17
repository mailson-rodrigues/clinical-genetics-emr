from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import exigir_acesso_modulo
from app.models.anamnese import Consulta, Resposta
from app.models.hipotese import HipoteseDiagnostica, FonteHipotese
from app.models.profissional import Profissional
from app.rate_limit import limiter
from app.schemas.hipotese import HipoteseDiagnosticaResponse
from app.services.ia_hipoteses import gerar_hipoteses, buscar_mais_fontes

router = APIRouter(prefix="/consultas", tags=["Hipóteses Diagnósticas"])


def _montar_perguntas_e_respostas(db: Session, consulta_id: int) -> list[dict]:
    respostas = db.query(Resposta).filter(Resposta.consulta_id == consulta_id).all()
    return [
        {
            "categoria": resposta.pergunta.categoria,
            "pergunta": resposta.pergunta.texto,
            "resposta": resposta.resposta_texto,
        }
        for resposta in respostas
    ]


@router.post("/{consulta_id}/hipoteses", response_model=List[HipoteseDiagnosticaResponse], status_code=201)
@limiter.limit("20/minute")
def gerar_hipoteses_diagnosticas(
    request: Request,
    consulta_id: int,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(exigir_acesso_modulo("consultas")),
):
    """
    Uses AI (with web search, restricted to PubMed/SciELO/Google
    Scholar/OMIM/Orphanet/GARD-NIH/MedlinePlus) to raise
    diagnostic hypotheses from the anamnesis answers. Each
    hypothesis comes with up to 5 sources by default. Requires login. Limited to
    20 requests/minute per IP.
    """
    consulta = db.query(Consulta).filter(Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")

    perguntas_e_respostas = _montar_perguntas_e_respostas(db, consulta_id)
    if not perguntas_e_respostas:
        raise HTTPException(
            status_code=400,
            detail="Essa consulta ainda não tem respostas registradas."
        )

    try:
        hipoteses_extraidas = gerar_hipoteses(consulta.condicao_investigada, perguntas_e_respostas)
    except ValueError as erro:
        raise HTTPException(status_code=502, detail=str(erro))

    novas_hipoteses = []
    for posicao, hipotese_extraida in enumerate(hipoteses_extraidas.hipoteses, start=1):
        nova_hipotese = HipoteseDiagnostica(
            consulta_id=consulta_id,
            condicao=hipotese_extraida.condicao,
            justificativa=hipotese_extraida.justificativa,
            cid_sugerido=hipotese_extraida.cid_sugerido,
            # "ordem" comes from the position in which the AI returned the hypothesis (already
            # instructed in the prompt to sort from most to least
            # likely) - it is not a separate field requested from the AI, so as not to
            # risk duplicated/out-of-sequence values.
            ordem=posicao,
        )
        db.add(nova_hipotese)
        db.flush()  # guarantees nova_hipotese.id before creating the sources

        for fonte in hipotese_extraida.fontes[:5]:
            db.add(FonteHipotese(
                hipotese_id=nova_hipotese.id,
                titulo=fonte.titulo,
                url=fonte.url,
                origem=fonte.origem,
            ))
        novas_hipoteses.append(nova_hipotese)

    db.commit()
    for hipotese in novas_hipoteses:
        db.refresh(hipotese)
    return novas_hipoteses


@router.get("/{consulta_id}/hipoteses", response_model=List[HipoteseDiagnosticaResponse])
def listar_hipoteses_diagnosticas(consulta_id: int, db: Session = Depends(get_db)):
    """Lists the diagnostic hypotheses already generated for a consultation."""
    consulta = db.query(Consulta).filter(Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")

    return (
        db.query(HipoteseDiagnostica)
        .filter(HipoteseDiagnostica.consulta_id == consulta_id)
        .order_by(HipoteseDiagnostica.ordem)
        .all()
    )


@router.post(
    "/{consulta_id}/hipoteses/{hipotese_id}/mais-fontes",
    response_model=HipoteseDiagnosticaResponse,
)
@limiter.limit("20/minute")
def buscar_mais_fontes_hipotese(
    request: Request,
    consulta_id: int,
    hipotese_id: int,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(exigir_acesso_modulo("consultas")),
):
    """
    Calls the AI again for this specific hypothesis, passing the
    existing condition and justification as context, asking
    specifically for up to 5 NEW sources (without repeating those already
    listed) - appends the new rows to the sources table, without
    replacing the existing ones. Requires login. Limited to 20
    requests/minute per IP (same module and limit as the initial
    generation).
    """
    hipotese = db.query(HipoteseDiagnostica).filter(
        HipoteseDiagnostica.id == hipotese_id,
        HipoteseDiagnostica.consulta_id == consulta_id,
    ).first()
    if not hipotese:
        raise HTTPException(status_code=404, detail="Hipótese não encontrada nessa consulta.")

    fontes_existentes = [{"url": fonte.url} for fonte in hipotese.fontes]

    try:
        novas_fontes = buscar_mais_fontes(hipotese.condicao, hipotese.justificativa, fontes_existentes)
    except ValueError as erro:
        raise HTTPException(status_code=502, detail=str(erro))

    for fonte in novas_fontes[:5]:
        db.add(FonteHipotese(
            hipotese_id=hipotese.id,
            titulo=fonte.titulo,
            url=fonte.url,
            origem=fonte.origem,
        ))

    db.commit()
    db.refresh(hipotese)
    return hipotese
