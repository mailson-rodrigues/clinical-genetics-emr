from app.models.perfil_acesso import Modulo, PerfilAcesso, PerfilAcessoModulo
from app.models.profissional import Profissional
from app.services.seguranca import gerar_hash_senha


def cabecalho(token):
    return {"Authorization": f"Bearer {token}"}


def _criar_modulos_basicos(db_session):
    """
    Idempotente: a fixture `profissional_token`/`profissional_info` (ver
    tests/conftest.py) já cria esses mesmos 5 módulos como efeito
    colateral (para montar o "Perfil Total (testes)") - reaproveita se
    já existirem, em vez de tentar duplicar e violar a unique constraint
    de Modulo.codigo.
    """
    modulos = {}
    for codigo, nome in [
        ("pacientes", "Pacientes"),
        ("consultas", "Consultas e Anamnese"),
        ("historico_clinico", "Histórico Clínico"),
        ("encaminhamentos", "Encaminhamentos"),
        ("exames", "Exames"),
    ]:
        modulo = db_session.query(Modulo).filter(Modulo.codigo == codigo).first()
        if not modulo:
            modulo = Modulo(codigo=codigo, nome=nome)
            db_session.add(modulo)
            db_session.flush()
        modulos[codigo] = modulo
    db_session.commit()
    return modulos


# =====================================================================
# Módulos (catálogo, só leitura, admin-only)
# =====================================================================

def test_listar_modulos_requer_admin(client, db_session, profissional_token, admin_token):
    _criar_modulos_basicos(db_session)

    resposta_profissional = client.get("/modulos/", headers=cabecalho(profissional_token))
    assert resposta_profissional.status_code == 403

    resposta_admin = client.get("/modulos/", headers=cabecalho(admin_token))
    assert resposta_admin.status_code == 200
    assert len(resposta_admin.json()) == 5


# =====================================================================
# CRUD de perfil de acesso (admin-only)
# =====================================================================

def test_crud_perfil_acesso(client, profissional_token, admin_token):
    resposta_profissional = client.post(
        "/perfis-acesso/", json={"nome": "Recepcionista"}, headers=cabecalho(profissional_token)
    )
    assert resposta_profissional.status_code == 403

    criado = client.post(
        "/perfis-acesso/",
        json={"nome": "Recepcionista", "descricao": "Acesso básico"},
        headers=cabecalho(admin_token),
    )
    assert criado.status_code == 201
    perfil = criado.json()
    assert perfil["nome"] == "Recepcionista"
    assert perfil["modulos"] == []

    # Não assume que "Recepcionista" é o único perfil existente - o
    # fixture `profissional_token` também cria um "Perfil Total (testes)"
    # como efeito colateral (ver tests/conftest.py).
    listagem = client.get("/perfis-acesso/", headers=cabecalho(admin_token))
    assert listagem.status_code == 200
    assert "Recepcionista" in [p["nome"] for p in listagem.json()]

    busca = client.get(f"/perfis-acesso/{perfil['id']}", headers=cabecalho(admin_token))
    assert busca.status_code == 200
    assert busca.json()["nome"] == "Recepcionista"

    atualizado = client.put(
        f"/perfis-acesso/{perfil['id']}",
        json={"descricao": "Nova descrição"},
        headers=cabecalho(admin_token),
    )
    assert atualizado.status_code == 200
    assert atualizado.json()["descricao"] == "Nova descrição"

    remocao = client.delete(f"/perfis-acesso/{perfil['id']}", headers=cabecalho(admin_token))
    assert remocao.status_code == 204

    busca_removido = client.get(f"/perfis-acesso/{perfil['id']}", headers=cabecalho(admin_token))
    assert busca_removido.status_code == 404


def test_criar_perfil_com_nome_duplicado(client, admin_token):
    client.post("/perfis-acesso/", json={"nome": "Recepcionista"}, headers=cabecalho(admin_token))
    resposta = client.post("/perfis-acesso/", json={"nome": "Recepcionista"}, headers=cabecalho(admin_token))
    assert resposta.status_code == 400


# =====================================================================
# Vincular/desvincular módulo
# =====================================================================

def test_vincular_e_desvincular_modulo(client, db_session, admin_token):
    modulos = _criar_modulos_basicos(db_session)
    perfil = client.post(
        "/perfis-acesso/", json={"nome": "Recepcionista"}, headers=cabecalho(admin_token)
    ).json()

    vinculado = client.post(
        f"/perfis-acesso/{perfil['id']}/modulos",
        json={"modulo_id": modulos["pacientes"].id},
        headers=cabecalho(admin_token),
    )
    assert vinculado.status_code == 201
    assert len(vinculado.json()["modulos"]) == 1
    assert vinculado.json()["modulos"][0]["codigo"] == "pacientes"

    # Vincular de novo o mesmo módulo não deve duplicar
    vinculado_de_novo = client.post(
        f"/perfis-acesso/{perfil['id']}/modulos",
        json={"modulo_id": modulos["pacientes"].id},
        headers=cabecalho(admin_token),
    )
    assert vinculado_de_novo.status_code == 201
    assert len(vinculado_de_novo.json()["modulos"]) == 1

    desvinculado = client.delete(
        f"/perfis-acesso/{perfil['id']}/modulos/{modulos['pacientes'].id}",
        headers=cabecalho(admin_token),
    )
    assert desvinculado.status_code == 204

    busca = client.get(f"/perfis-acesso/{perfil['id']}", headers=cabecalho(admin_token)).json()
    assert busca["modulos"] == []


def test_remover_perfil_vinculado_a_profissional_e_bloqueado(client, db_session, admin_token):
    perfil = client.post(
        "/perfis-acesso/", json={"nome": "Recepcionista"}, headers=cabecalho(admin_token)
    ).json()

    profissional = Profissional(
        nome="Fulana Recepção",
        email="recepcao.vinculada@exemplo.com",
        senha_hash=gerar_hash_senha("senha123"),
        nivel_acesso="profissional",
        perfil_acesso_id=perfil["id"],
    )
    db_session.add(profissional)
    db_session.commit()

    resposta = client.delete(f"/perfis-acesso/{perfil['id']}", headers=cabecalho(admin_token))
    assert resposta.status_code == 400


# =====================================================================
# exigir_acesso_modulo - comportamento de restrição de fato
# =====================================================================

def _criar_e_logar_recepcionista(client, db_session):
    modulos = _criar_modulos_basicos(db_session)

    perfil = PerfilAcesso(nome="Recepcionista")
    db_session.add(perfil)
    db_session.flush()
    db_session.add(PerfilAcessoModulo(perfil_acesso_id=perfil.id, modulo_id=modulos["pacientes"].id))
    db_session.commit()

    profissional = Profissional(
        nome="Recepcionista Teste",
        email="recepcionista.teste@exemplo.com",
        senha_hash=gerar_hash_senha("senha123"),
        nivel_acesso="profissional",
        perfil_acesso_id=perfil.id,
    )
    db_session.add(profissional)
    db_session.commit()

    login = client.post(
        "/auth/login", json={"email": "recepcionista.teste@exemplo.com", "senha": "senha123"}
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def test_perfil_recepcionista_acessa_pacientes_mas_nao_consultas_ou_encaminhamentos(
    client, db_session, paciente_exemplo
):
    token = _criar_e_logar_recepcionista(client, db_session)

    # Pacientes: rota de criação não é gated por perfil (não foi alterada
    # nesta etapa - fica como já era), então qualquer um consegue, inclusive
    # a recepcionista, confirmando que ela "consegue fazer algo em pacientes".
    resposta_paciente = client.post(
        "/pacientes/",
        json={"nome": "Outro Paciente", "data_nascimento": "1980-01-01", "sexo": "M", "documento": "22233344455"},
        headers=cabecalho(token),
    )
    assert resposta_paciente.status_code == 201

    # Consultas: módulo NÃO liberado para o perfil Recepcionista -> 403
    resposta_consulta = client.post(
        "/consultas/",
        json={"paciente_id": paciente_exemplo["id"], "condicao_investigada": "teste"},
        headers=cabecalho(token),
    )
    assert resposta_consulta.status_code == 403

    # Encaminhamentos: também não liberado -> 403 (mesmo que a consulta
    # não exista de verdade, a checagem de perfil roda antes de tudo)
    resposta_encaminhamento = client.post(
        "/consultas/999/encaminhamentos",
        json={"motivo": "teste"},
        headers=cabecalho(token),
    )
    assert resposta_encaminhamento.status_code == 403


def test_administrador_acessa_tudo_independente_de_perfil(client, admin_token, paciente_exemplo):
    """Administrador nunca tem perfil_acesso_id, mas continua com acesso total."""
    resposta_consulta = client.post(
        "/consultas/",
        json={"paciente_id": paciente_exemplo["id"], "condicao_investigada": "teste"},
        headers=cabecalho(admin_token),
    )
    assert resposta_consulta.status_code == 201

    resposta_encaminhamento = client.post(
        f"/consultas/{resposta_consulta.json()['id']}/encaminhamentos",
        json={"motivo": "teste"},
        headers=cabecalho(admin_token),
    )
    assert resposta_encaminhamento.status_code == 201


def test_profissional_sem_perfil_algum_recebe_403(client, db_session, paciente_exemplo):
    """Profissional comum sem NENHUM perfil_acesso_id vinculado não acessa módulos restritos."""
    profissional = Profissional(
        nome="Sem Perfil",
        email="sem.perfil@exemplo.com",
        senha_hash=gerar_hash_senha("senha123"),
        nivel_acesso="profissional",
        perfil_acesso_id=None,
    )
    db_session.add(profissional)
    db_session.commit()

    login = client.post("/auth/login", json={"email": "sem.perfil@exemplo.com", "senha": "senha123"})
    token = login.json()["access_token"]

    resposta = client.post(
        "/consultas/",
        json={"paciente_id": paciente_exemplo["id"], "condicao_investigada": "teste"},
        headers=cabecalho(token),
    )
    assert resposta.status_code == 403
