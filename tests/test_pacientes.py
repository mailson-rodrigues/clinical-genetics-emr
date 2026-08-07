def _dados_paciente(documento="22222222222", nome="Fulano de Tal"):
    return {
        "nome": nome,
        "data_nascimento": "1985-05-20",
        "sexo": "M",
        "documento": documento,
    }


def test_criar_paciente(client):
    resposta = client.post("/pacientes/", json=_dados_paciente())

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["documento"] == "22222222222"
    assert corpo["id"]


def test_listar_pacientes(client, paciente_exemplo):
    resposta = client.get("/pacientes/")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["id"] == paciente_exemplo["id"]


def test_listar_pacientes_paginado(client):
    for numero in range(3):
        client.post("/pacientes/", json=_dados_paciente(documento=f"3000000000{numero}"))

    resposta = client.get("/pacientes/", params={"skip": 1, "limit": 1})

    assert resposta.status_code == 200
    assert resposta.headers["X-Total-Count"] == "3"
    assert len(resposta.json()) == 1


def test_listar_pacientes_limit_maximo(client):
    resposta = client.get("/pacientes/", params={"limit": 500})

    assert resposta.status_code == 422


def test_listar_pacientes_busca_por_nome_parcial(client):
    client.post("/pacientes/", json=_dados_paciente(documento="40000000001", nome="Maria da Silva"))
    client.post("/pacientes/", json=_dados_paciente(documento="40000000002", nome="João Souza"))

    resposta = client.get("/pacientes/", params={"busca": "maria"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["nome"] == "Maria da Silva"


def test_listar_pacientes_busca_por_documento_parcial(client):
    client.post("/pacientes/", json=_dados_paciente(documento="40000000003", nome="Paciente A"))
    client.post("/pacientes/", json=_dados_paciente(documento="40000000004", nome="Paciente B"))

    resposta = client.get("/pacientes/", params={"busca": "0003"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["documento"] == "40000000003"


def test_listar_pacientes_busca_sem_resultado(client, paciente_exemplo):
    resposta = client.get("/pacientes/", params={"busca": "nome que nao existe"})

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_buscar_paciente_por_id(client, paciente_exemplo):
    resposta = client.get(f"/pacientes/{paciente_exemplo['id']}")

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == paciente_exemplo["nome"]


def test_buscar_paciente_inexistente(client):
    resposta = client.get("/pacientes/9999")

    assert resposta.status_code == 404


def test_criar_paciente_com_cpf_duplicado(client, paciente_exemplo):
    resposta = client.post("/pacientes/", json=_dados_paciente(documento=paciente_exemplo["documento"]))

    assert resposta.status_code == 400


def test_editar_paciente_sem_ser_admin(client, paciente_exemplo, profissional_token):
    resposta = client.put(
        f"/pacientes/{paciente_exemplo['id']}",
        json={"nome": "Nome Corrigido"},
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 403


def test_editar_paciente_como_admin(client, paciente_exemplo, admin_token):
    resposta = client.put(
        f"/pacientes/{paciente_exemplo['id']}",
        json={"nome": "Nome Corrigido"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Nome Corrigido"


def test_remover_paciente_sem_ser_admin(client, paciente_exemplo, profissional_token):
    resposta = client.delete(
        f"/pacientes/{paciente_exemplo['id']}",
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 403


def test_remover_paciente_como_admin(client, paciente_exemplo, admin_token):
    """
    Remoção é soft delete: o registro continua existindo (buscável por id,
    com ativo=False), mas some da listagem padrão.
    """
    resposta = client.delete(
        f"/pacientes/{paciente_exemplo['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert resposta.status_code == 204

    resposta_get = client.get(f"/pacientes/{paciente_exemplo['id']}")
    assert resposta_get.status_code == 200
    assert resposta_get.json()["ativo"] is False

    listagem = client.get("/pacientes/").json()
    assert paciente_exemplo["id"] not in [p["id"] for p in listagem]


def test_listar_pacientes_nao_traz_inativos_por_padrao(client, paciente_exemplo, admin_token):
    client.delete(f"/pacientes/{paciente_exemplo['id']}", headers={"Authorization": f"Bearer {admin_token}"})

    resposta = client.get("/pacientes/")

    assert resposta.status_code == 200
    assert resposta.json() == []
    assert resposta.headers["X-Total-Count"] == "0"


def test_listar_pacientes_incluir_inativos_sem_ser_admin(client, paciente_exemplo, admin_token, profissional_token):
    client.delete(f"/pacientes/{paciente_exemplo['id']}", headers={"Authorization": f"Bearer {admin_token}"})

    resposta = client.get(
        "/pacientes/",
        params={"incluir_inativos": "true"},
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 403


def test_listar_pacientes_incluir_inativos_sem_login(client, paciente_exemplo, admin_token):
    client.delete(f"/pacientes/{paciente_exemplo['id']}", headers={"Authorization": f"Bearer {admin_token}"})

    resposta = client.get("/pacientes/", params={"incluir_inativos": "true"})

    assert resposta.status_code == 403


def test_listar_pacientes_incluir_inativos_como_admin(client, paciente_exemplo, admin_token):
    client.delete(f"/pacientes/{paciente_exemplo['id']}", headers={"Authorization": f"Bearer {admin_token}"})

    resposta = client.get(
        "/pacientes/",
        params={"incluir_inativos": "true"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["ativo"] is False


def test_reativar_paciente_via_put(client, paciente_exemplo, admin_token):
    client.delete(f"/pacientes/{paciente_exemplo['id']}", headers={"Authorization": f"Bearer {admin_token}"})

    resposta = client.put(
        f"/pacientes/{paciente_exemplo['id']}",
        json={"ativo": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["ativo"] is True

    listagem = client.get("/pacientes/").json()
    assert paciente_exemplo["id"] in [p["id"] for p in listagem]
