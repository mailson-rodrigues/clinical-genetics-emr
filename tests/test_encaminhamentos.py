def test_criar_encaminhamento(client, consulta_exemplo, profissional_info):
    resposta = client.post(
        f"/consultas/{consulta_exemplo['id']}/encaminhamentos",
        json={"motivo": "Suspeita de síndrome hereditária, encaminhar para oncogenética."},
        headers={"Authorization": f"Bearer {profissional_info['token']}"},
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["consulta_id"] == consulta_exemplo["id"]
    assert corpo["status"] == "pendente"
    assert corpo["profissional_id"] == profissional_info["profissional_id"]


def test_listar_encaminhamentos(client, consulta_exemplo, profissional_token):
    client.post(
        f"/consultas/{consulta_exemplo['id']}/encaminhamentos",
        json={"motivo": "Motivo de teste"},
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    resposta = client.get(f"/consultas/{consulta_exemplo['id']}/encaminhamentos")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


def test_atualizar_status_encaminhamento(client, consulta_exemplo, profissional_token):
    criado = client.post(
        f"/consultas/{consulta_exemplo['id']}/encaminhamentos",
        json={"motivo": "Motivo de teste"},
        headers={"Authorization": f"Bearer {profissional_token}"},
    ).json()

    resposta = client.put(
        f"/consultas/{consulta_exemplo['id']}/encaminhamentos/{criado['id']}",
        json={"status": "concluido"},
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "concluido"


def test_atualizar_status_invalido(client, consulta_exemplo, profissional_token):
    criado = client.post(
        f"/consultas/{consulta_exemplo['id']}/encaminhamentos",
        json={"motivo": "Motivo de teste"},
        headers={"Authorization": f"Bearer {profissional_token}"},
    ).json()

    resposta = client.put(
        f"/consultas/{consulta_exemplo['id']}/encaminhamentos/{criado['id']}",
        json={"status": "invalido"},
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 400


def test_remover_encaminhamento(client, consulta_exemplo, profissional_token):
    criado = client.post(
        f"/consultas/{consulta_exemplo['id']}/encaminhamentos",
        json={"motivo": "Motivo de teste"},
        headers={"Authorization": f"Bearer {profissional_token}"},
    ).json()

    resposta = client.delete(
        f"/consultas/{consulta_exemplo['id']}/encaminhamentos/{criado['id']}",
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 204

    listagem = client.get(f"/consultas/{consulta_exemplo['id']}/encaminhamentos").json()
    assert listagem == []
