def _gerar_heredograma(client, consulta_id, pergunta_id, token, mocker, heredograma_exemplo):
    client.post(
        f"/consultas/{consulta_id}/respostas",
        json={"pergunta_id": pergunta_id, "resposta_texto": "Câncer de próstata no pai."},
        headers={"Authorization": f"Bearer {token}"},
    )
    mocker.patch("app.routes.consulta.extrair_heredograma", return_value=heredograma_exemplo)
    resposta = client.post(
        f"/consultas/{consulta_id}/gerar-heredograma",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def test_criar_exame_vinculado_a_individuo(
    client, consulta_exemplo, pergunta_exemplo, profissional_info, mocker, heredograma_exemplo
):
    heredograma = _gerar_heredograma(
        client, consulta_exemplo["id"], pergunta_exemplo.id, profissional_info["token"], mocker, heredograma_exemplo
    )
    individuo_id = heredograma["individuos"][0]["id"]

    resposta = client.post(
        f"/consultas/{consulta_exemplo['id']}/exames",
        json={"tipo_exame": "Painel BRCA1/BRCA2", "individuo_id": individuo_id},
        headers={"Authorization": f"Bearer {profissional_info['token']}"},
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["individuo_id"] == individuo_id
    assert corpo["status"] == "solicitado"
    assert corpo["profissional_id"] == profissional_info["profissional_id"]


def test_criar_exame_sem_vincular_individuo(client, consulta_exemplo, profissional_token):
    resposta = client.post(
        f"/consultas/{consulta_exemplo['id']}/exames",
        json={"tipo_exame": "Cariótipo"},
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["individuo_id"] is None


def test_criar_exame_vinculado_a_individuo_de_outra_consulta(
    client, consulta_exemplo, pergunta_exemplo, profissional_info, mocker, heredograma_exemplo, paciente_exemplo
):
    heredograma = _gerar_heredograma(
        client, consulta_exemplo["id"], pergunta_exemplo.id, profissional_info["token"], mocker, heredograma_exemplo
    )
    individuo_de_outra_consulta = heredograma["individuos"][0]["id"]

    outra_consulta = client.post(
        "/consultas/",
        json={"paciente_id": paciente_exemplo["id"], "condicao_investigada": "Outra condição"},
        headers={"Authorization": f"Bearer {profissional_info['token']}"},
    ).json()

    resposta = client.post(
        f"/consultas/{outra_consulta['id']}/exames",
        json={"tipo_exame": "Cariótipo", "individuo_id": individuo_de_outra_consulta},
        headers={"Authorization": f"Bearer {profissional_info['token']}"},
    )

    assert resposta.status_code == 404


def test_criar_exame_com_individuo_inexistente(client, consulta_exemplo, profissional_token):
    resposta = client.post(
        f"/consultas/{consulta_exemplo['id']}/exames",
        json={"tipo_exame": "Cariótipo", "individuo_id": 9999},
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 404


def test_criar_exame_sem_login(client, consulta_exemplo):
    resposta = client.post(
        f"/consultas/{consulta_exemplo['id']}/exames",
        json={"tipo_exame": "Cariótipo"},
    )

    assert resposta.status_code == 401


def test_listar_exames_sem_login(client, consulta_exemplo, profissional_token):
    client.post(
        f"/consultas/{consulta_exemplo['id']}/exames",
        json={"tipo_exame": "Cariótipo"},
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    resposta = client.get(f"/consultas/{consulta_exemplo['id']}/exames")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


def test_atualizar_status_exame(client, consulta_exemplo, profissional_token):
    criado = client.post(
        f"/consultas/{consulta_exemplo['id']}/exames",
        json={"tipo_exame": "Cariótipo"},
        headers={"Authorization": f"Bearer {profissional_token}"},
    ).json()

    resposta = client.put(
        f"/consultas/{consulta_exemplo['id']}/exames/{criado['id']}",
        json={"status": "concluido", "resultado": "46,XX normal", "data_resultado": "2026-07-25"},
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "concluido"
    assert corpo["resultado"] == "46,XX normal"
    assert corpo["data_resultado"] == "2026-07-25"


def test_atualizar_status_invalido(client, consulta_exemplo, profissional_token):
    criado = client.post(
        f"/consultas/{consulta_exemplo['id']}/exames",
        json={"tipo_exame": "Cariótipo"},
        headers={"Authorization": f"Bearer {profissional_token}"},
    ).json()

    resposta = client.put(
        f"/consultas/{consulta_exemplo['id']}/exames/{criado['id']}",
        json={"status": "invalido"},
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 400


def test_remover_exame(client, consulta_exemplo, profissional_token):
    criado = client.post(
        f"/consultas/{consulta_exemplo['id']}/exames",
        json={"tipo_exame": "Cariótipo"},
        headers={"Authorization": f"Bearer {profissional_token}"},
    ).json()

    resposta = client.delete(
        f"/consultas/{consulta_exemplo['id']}/exames/{criado['id']}",
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 204

    listagem = client.get(f"/consultas/{consulta_exemplo['id']}/exames").json()
    assert listagem == []
