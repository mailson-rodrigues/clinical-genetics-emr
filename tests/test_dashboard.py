from datetime import date, datetime, timedelta, timezone

from app.models.anamnese import Consulta
from app.models.encaminhamento import Encaminhamento
from app.models.exame import Exame
from app.models.paciente import Paciente


def _criar_paciente(db_session, nome, ativo=True):
    paciente = Paciente(
        nome=nome,
        data_nascimento=date(1990, 1, 1),
        sexo="F",
        documento=f"doc-{nome}",
        ativo=ativo,
    )
    db_session.add(paciente)
    db_session.commit()
    db_session.refresh(paciente)
    return paciente


def _criar_consulta(db_session, paciente, condicao, criado_em=None):
    consulta = Consulta(paciente_id=paciente.id, condicao_investigada=condicao)
    db_session.add(consulta)
    db_session.commit()
    db_session.refresh(consulta)

    if criado_em is not None:
        consulta.criado_em = criado_em
        db_session.commit()
        db_session.refresh(consulta)

    return consulta


def test_resumo_dashboard_conta_apenas_o_que_deve(client, db_session, profissional_token):
    paciente_ativo_1 = _criar_paciente(db_session, "Ativo Um", ativo=True)
    paciente_ativo_2 = _criar_paciente(db_session, "Ativo Dois", ativo=True)
    _criar_paciente(db_session, "Inativo Um", ativo=False)

    agora = datetime.now(timezone.utc)
    algum_dia_do_mes_passado = agora.replace(day=1) - timedelta(days=5)

    # criado_em explícito (em vez de confiar no relógio real em sequência)
    # para a ordenação "mais recente primeiro" não depender da precisão de
    # timestamp do SQLite - dois inserts na mesma sessão de teste podem
    # cair no mesmo segundo e empatar.
    consulta_mes_atual_1 = _criar_consulta(db_session, paciente_ativo_1, "Condição A", criado_em=agora - timedelta(minutes=5))
    consulta_mes_atual_2 = _criar_consulta(db_session, paciente_ativo_2, "Condição B", criado_em=agora)
    _criar_consulta(db_session, paciente_ativo_1, "Condição do mês passado", criado_em=algum_dia_do_mes_passado)

    db_session.add_all([
        Encaminhamento(consulta_id=consulta_mes_atual_1.id, motivo="Motivo pendente", status="pendente"),
        Encaminhamento(consulta_id=consulta_mes_atual_1.id, motivo="Motivo concluído", status="concluido"),
        Exame(consulta_id=consulta_mes_atual_1.id, tipo_exame="Exame solicitado", status="solicitado"),
        Exame(consulta_id=consulta_mes_atual_2.id, tipo_exame="Exame em andamento", status="em_andamento"),
        Exame(consulta_id=consulta_mes_atual_2.id, tipo_exame="Exame concluído", status="concluido"),
    ])
    db_session.commit()

    resposta = client.get("/dashboard/resumo", headers={"Authorization": f"Bearer {profissional_token}"})

    assert resposta.status_code == 200
    corpo = resposta.json()

    # 2 pacientes ativos - o inativo não conta
    assert corpo["total_pacientes_ativos"] == 2
    # 2 consultas deste mês - a do mês passado não conta
    assert corpo["consultas_mes_atual"] == 2
    # 1 encaminhamento pendente - o concluído não conta
    assert corpo["encaminhamentos_pendentes"] == 1
    # 2 exames aguardando (solicitado + em_andamento) - o concluído não conta
    assert corpo["exames_aguardando"] == 2

    assert len(corpo["atividade_recente"]) == 3
    nomes_atividade = [item["paciente_nome"] for item in corpo["atividade_recente"]]
    assert nomes_atividade[0] == "Ativo Dois"  # mais recente primeiro


def test_resumo_dashboard_sem_dados(client, profissional_token):
    resposta = client.get("/dashboard/resumo", headers={"Authorization": f"Bearer {profissional_token}"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total_pacientes_ativos"] == 0
    assert corpo["consultas_mes_atual"] == 0
    assert corpo["encaminhamentos_pendentes"] == 0
    assert corpo["exames_aguardando"] == 0
    assert corpo["atividade_recente"] == []


def test_resumo_dashboard_requer_login(client):
    resposta = client.get("/dashboard/resumo")

    assert resposta.status_code == 401
