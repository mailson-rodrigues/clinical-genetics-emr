"""
Testes focados especificamente na diferença de comportamento entre
nivel_acesso="profissional" e "administrador" nas rotas restritas a
administrador (dependência `exigir_administrador` em app/dependencies.py).
"""


def cabecalho(token):
    return {"Authorization": f"Bearer {token}"}


def test_editar_paciente_profissional_vs_admin(client, paciente_exemplo, profissional_token, admin_token):
    resposta_profissional = client.put(
        f"/pacientes/{paciente_exemplo['id']}",
        json={"nome": "Tentativa Profissional"},
        headers=cabecalho(profissional_token),
    )
    assert resposta_profissional.status_code == 403

    resposta_admin = client.put(
        f"/pacientes/{paciente_exemplo['id']}",
        json={"nome": "Ajuste Admin"},
        headers=cabecalho(admin_token),
    )
    assert resposta_admin.status_code == 200


def test_remover_paciente_profissional_vs_admin(client, paciente_exemplo, profissional_token, admin_token):
    resposta_profissional = client.delete(
        f"/pacientes/{paciente_exemplo['id']}",
        headers=cabecalho(profissional_token),
    )
    assert resposta_profissional.status_code == 403

    resposta_admin = client.delete(
        f"/pacientes/{paciente_exemplo['id']}",
        headers=cabecalho(admin_token),
    )
    assert resposta_admin.status_code == 204


def test_editar_profissional_profissional_vs_admin(client, profissional_info, profissional_token, admin_token):
    alvo_id = profissional_info["profissional_id"]

    resposta_profissional = client.put(
        f"/profissionais/{alvo_id}",
        json={"registro_profissional": "CRM-000"},
        headers=cabecalho(profissional_token),
    )
    assert resposta_profissional.status_code == 403

    resposta_admin = client.put(
        f"/profissionais/{alvo_id}",
        json={"registro_profissional": "CRM-123"},
        headers=cabecalho(admin_token),
    )
    assert resposta_admin.status_code == 200
    assert resposta_admin.json()["registro_profissional"] == "CRM-123"


def test_criar_cid_profissional_vs_admin(client, profissional_token, admin_token):
    dados = {"codigo": "C61", "descricao": "Neoplasia maligna da próstata"}

    resposta_profissional = client.post("/cids/", json=dados, headers=cabecalho(profissional_token))
    assert resposta_profissional.status_code == 403

    resposta_admin = client.post("/cids/", json=dados, headers=cabecalho(admin_token))
    assert resposta_admin.status_code == 201


def test_criar_operadora_profissional_vs_admin(client, profissional_token, admin_token):
    dados = {"nome": "Unimed"}

    resposta_profissional = client.post("/operadoras/", json=dados, headers=cabecalho(profissional_token))
    assert resposta_profissional.status_code == 403

    resposta_admin = client.post("/operadoras/", json=dados, headers=cabecalho(admin_token))
    assert resposta_admin.status_code == 201


def test_listar_logs_profissional_vs_admin(client, profissional_token, admin_token):
    resposta_profissional = client.get("/logs/", headers=cabecalho(profissional_token))
    assert resposta_profissional.status_code == 403

    resposta_admin = client.get("/logs/", headers=cabecalho(admin_token))
    assert resposta_admin.status_code == 200
