from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import obter_profissional_atual
from app.models.anamnese import Consulta
from app.models.encaminhamento import Encaminhamento
from app.models.exame import Exame
from app.models.paciente import Paciente
from app.models.profissional import Profissional
from app.schemas.dashboard import AtividadeRecente, ResumoDashboard

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _inicio_do_mes_atual() -> datetime:
    agora = datetime.now(timezone.utc)
    return datetime(agora.year, agora.month, 1, tzinfo=timezone.utc)


def _inicio_do_proximo_mes(inicio_mes_atual: datetime) -> datetime:
    if inicio_mes_atual.month == 12:
        return inicio_mes_atual.replace(year=inicio_mes_atual.year + 1, month=1)
    return inicio_mes_atual.replace(month=inicio_mes_atual.month + 1)


@router.get("/resumo", response_model=ResumoDashboard)
def obter_resumo(
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(obter_profissional_atual),
):
    """
    Indicadores agregados para o dashboard (página inicial). Requer
    login, sem restrição de perfil/módulo - são só contadores, não
    dados individuais sensíveis.
    """
    inicio_mes = _inicio_do_mes_atual()
    inicio_proximo_mes = _inicio_do_proximo_mes(inicio_mes)

    total_pacientes_ativos = db.query(Paciente).filter(Paciente.ativo == True).count()  # noqa: E712

    consultas_mes_atual = (
        db.query(Consulta)
        .filter(Consulta.criado_em >= inicio_mes, Consulta.criado_em < inicio_proximo_mes)
        .count()
    )

    encaminhamentos_pendentes = (
        db.query(Encaminhamento).filter(Encaminhamento.status == "pendente").count()
    )

    exames_aguardando = (
        db.query(Exame).filter(Exame.status.in_(["solicitado", "em_andamento"])).count()
    )

    # Consulta não tem relationship para Paciente (só a FK paciente_id) -
    # join explícito trazendo os dois lados em vez de acessar
    # consulta.paciente.
    ultimas_consultas = (
        db.query(Consulta, Paciente)
        .join(Paciente, Paciente.id == Consulta.paciente_id)
        .order_by(Consulta.criado_em.desc())
        .limit(5)
        .all()
    )

    atividade_recente = [
        AtividadeRecente(
            consulta_id=consulta.id,
            paciente_nome=paciente.nome_social or paciente.nome,
            condicao_investigada=consulta.condicao_investigada,
            criado_em=consulta.criado_em,
        )
        for consulta, paciente in ultimas_consultas
    ]

    return ResumoDashboard(
        total_pacientes_ativos=total_pacientes_ativos,
        consultas_mes_atual=consultas_mes_atual,
        encaminhamentos_pendentes=encaminhamentos_pendentes,
        exames_aguardando=exames_aguardando,
        atividade_recente=atividade_recente,
    )
