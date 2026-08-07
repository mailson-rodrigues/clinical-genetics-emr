def cabecalho(token):
    return {"Authorization": f"Bearer {token}"}


# =====================================================================
# Alergias
# =====================================================================

def test_criar_alergia_sem_login(client, paciente_exemplo):
    resposta = client.post(f"/pacientes/{paciente_exemplo['id']}/alergias", json={"descricao": "Dipirona"})
    assert resposta.status_code == 401


def test_criar_listar_e_remover_alergia(client, paciente_exemplo, profissional_token):
    criada = client.post(
        f"/pacientes/{paciente_exemplo['id']}/alergias",
        json={"descricao": "Dipirona"},
        headers=cabecalho(profissional_token),
    )
    assert criada.status_code == 201
    item_id = criada.json()["id"]

    listagem = client.get(f"/pacientes/{paciente_exemplo['id']}/alergias", headers=cabecalho(profissional_token))
    assert listagem.status_code == 200
    assert len(listagem.json()) == 1

    remocao = client.delete(
        f"/pacientes/{paciente_exemplo['id']}/alergias/{item_id}", headers=cabecalho(profissional_token)
    )
    assert remocao.status_code == 204


# =====================================================================
# Cirurgias
# =====================================================================

def test_criar_cirurgia_sem_login(client, paciente_exemplo):
    resposta = client.post(f"/pacientes/{paciente_exemplo['id']}/cirurgias", json={"descricao": "Apendicectomia"})
    assert resposta.status_code == 401


def test_criar_listar_e_remover_cirurgia(client, paciente_exemplo, profissional_token):
    criada = client.post(
        f"/pacientes/{paciente_exemplo['id']}/cirurgias",
        json={"descricao": "Apendicectomia"},
        headers=cabecalho(profissional_token),
    )
    assert criada.status_code == 201
    item_id = criada.json()["id"]

    listagem = client.get(f"/pacientes/{paciente_exemplo['id']}/cirurgias", headers=cabecalho(profissional_token))
    assert listagem.status_code == 200
    assert len(listagem.json()) == 1

    remocao = client.delete(
        f"/pacientes/{paciente_exemplo['id']}/cirurgias/{item_id}", headers=cabecalho(profissional_token)
    )
    assert remocao.status_code == 204


# =====================================================================
# Históricos clínicos
# =====================================================================

def test_criar_historico_sem_login(client, paciente_exemplo):
    resposta = client.post(f"/pacientes/{paciente_exemplo['id']}/historicos", json={"descricao": "Hipertensão"})
    assert resposta.status_code == 401


def test_criar_listar_e_remover_historico(client, paciente_exemplo, profissional_token):
    criada = client.post(
        f"/pacientes/{paciente_exemplo['id']}/historicos",
        json={"descricao": "Hipertensão"},
        headers=cabecalho(profissional_token),
    )
    assert criada.status_code == 201
    item_id = criada.json()["id"]

    listagem = client.get(f"/pacientes/{paciente_exemplo['id']}/historicos", headers=cabecalho(profissional_token))
    assert listagem.status_code == 200
    assert len(listagem.json()) == 1

    remocao = client.delete(
        f"/pacientes/{paciente_exemplo['id']}/historicos/{item_id}", headers=cabecalho(profissional_token)
    )
    assert remocao.status_code == 204


# =====================================================================
# Doenças (com vínculo opcional a CID)
# =====================================================================

def test_criar_doenca_sem_login(client, paciente_exemplo):
    resposta = client.post(f"/pacientes/{paciente_exemplo['id']}/doencas", json={"descricao": "Câncer de mama"})
    assert resposta.status_code == 401


def test_criar_doenca_sem_cid(client, paciente_exemplo, profissional_token):
    resposta = client.post(
        f"/pacientes/{paciente_exemplo['id']}/doencas",
        json={"descricao": "Câncer de mama"},
        headers=cabecalho(profissional_token),
    )
    assert resposta.status_code == 201
    assert resposta.json()["cid_id"] is None


def test_criar_doenca_com_cid_valido(client, paciente_exemplo, profissional_token, admin_token):
    cid = client.post(
        "/cids/",
        json={"codigo": "C50", "descricao": "Neoplasia maligna da mama"},
        headers=cabecalho(admin_token),
    ).json()

    resposta = client.post(
        f"/pacientes/{paciente_exemplo['id']}/doencas",
        json={"descricao": "Câncer de mama", "cid_id": cid["id"]},
        headers=cabecalho(profissional_token),
    )
    assert resposta.status_code == 201
    assert resposta.json()["cid_id"] == cid["id"]


def test_criar_doenca_com_cid_invalido(client, paciente_exemplo, profissional_token):
    resposta = client.post(
        f"/pacientes/{paciente_exemplo['id']}/doencas",
        json={"descricao": "Câncer de mama", "cid_id": 9999},
        headers=cabecalho(profissional_token),
    )
    assert resposta.status_code == 404
