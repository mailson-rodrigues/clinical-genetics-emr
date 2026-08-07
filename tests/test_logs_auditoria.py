def test_acao_gera_entrada_no_log(client, admin_token):
    client.post(
        "/pacientes/",
        json={
            "nome": "Paciente Logado",
            "data_nascimento": "2000-01-01",
            "sexo": "F",
            "documento": "33333333333",
        },
    )

    resposta = client.get("/logs/", headers={"Authorization": f"Bearer {admin_token}"})

    assert resposta.status_code == 200
    logs = resposta.json()
    assert any(
        log["metodo"] == "POST" and log["caminho"] == "/pacientes/"
        for log in logs
    )


def test_log_registra_profissional_id_de_acao_autenticada(client, profissional_info, paciente_exemplo, admin_token):
    resposta_consulta = client.post(
        "/consultas/",
        json={"paciente_id": paciente_exemplo["id"], "condicao_investigada": "Teste de auditoria"},
        headers={"Authorization": f"Bearer {profissional_info['token']}"},
    )
    assert resposta_consulta.status_code == 201

    logs = client.get(
        "/logs/",
        params={"profissional_id": profissional_info["profissional_id"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    assert any(
        log["metodo"] == "POST" and log["caminho"] == "/consultas/" and log["profissional_id"] == profissional_info["profissional_id"]
        for log in logs
    )


def test_logs_restrito_a_administrador(client, profissional_token, admin_token):
    resposta_profissional = client.get("/logs/", headers={"Authorization": f"Bearer {profissional_token}"})
    assert resposta_profissional.status_code == 403

    resposta_admin = client.get("/logs/", headers={"Authorization": f"Bearer {admin_token}"})
    assert resposta_admin.status_code == 200
