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
    Usa a IA (com busca na web, restrita a PubMed/SciELO/Google
    Acadêmico/OMIM/Orphanet/GARD-NIH/MedlinePlus) para levantar
    hipóteses diagnósticas a partir das respostas da anamnese. Cada
    hipótese vem com até 5 fontes por padrão. Requer login. Limitada a
    20 requisições/minuto por IP.
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
            # "ordem" vem da posição em que a IA devolveu a hipótese (já
            # instruída no prompt a ordenar da mais para a menos
            # provável) - não é um campo separado pedido à IA, para não
            # arriscar valores duplicados/fora de sequência.
            ordem=posicao,
        )
        db.add(nova_hipotese)
        db.flush()  # garante nova_hipotese.id antes de criar as fontes

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
    """Lista as hipóteses diagnósticas já geradas para uma consulta."""
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
    Chama a IA de novo para essa hipótese específica, passando a
    condição e a justificativa já existentes como contexto, pedindo
    especificamente por até 5 fontes NOVAS (sem repetir as já
    listadas) - anexa as novas linhas à tabela de fontes, sem
    substituir as existentes. Requer login. Limitada a 20
    requisições/minuto por IP (mesmo módulo e limite da geração
    inicial).
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
