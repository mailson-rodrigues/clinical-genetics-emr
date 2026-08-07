def test_criar_consulta_sem_login(client, paciente_exemplo):
    resposta = client.post(
        "/consultas/",
        json={"paciente_id": paciente_exemplo["id"], "condicao_investigada": "Câncer de mama hereditário"},
    )

    assert resposta.status_code == 401


def test_criar_consulta_com_login(client, paciente_exemplo, profissional_info):
    resposta = client.post(
        "/consultas/",
        json={"paciente_id": paciente_exemplo["id"], "condicao_investigada": "Câncer de mama hereditário"},
        headers={"Authorization": f"Bearer {profissional_info['token']}"},
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["paciente_id"] == paciente_exemplo["id"]
    assert corpo["profissional_id"] == profissional_info["profissional_id"]
    assert corpo["status"] == "em_andamento"


def test_listar_consultas_paginado(client, paciente_exemplo, profissional_token):
    for _ in range(3):
        client.post(
            "/consultas/",
            json={"paciente_id": paciente_exemplo["id"], "condicao_investigada": "Condição de teste"},
            headers={"Authorization": f"Bearer {profissional_token}"},
        )

    resposta = client.get("/consultas/", params={"skip": 1, "limit": 1})

    assert resposta.status_code == 200
    assert resposta.headers["X-Total-Count"] == "3"
    assert len(resposta.json()) == 1


def test_registrar_resposta_anamnese(client, consulta_exemplo, pergunta_exemplo, profissional_token):
    resposta = client.post(
        f"/consultas/{consulta_exemplo['id']}/respostas",
        json={"pergunta_id": pergunta_exemplo.id, "resposta_texto": "Câncer de mama na avó materna."},
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["consulta_id"] == consulta_exemplo["id"]
    assert corpo["resposta_texto"] == "Câncer de mama na avó materna."


def test_editar_resposta_anamnese(client, consulta_exemplo, pergunta_exemplo, profissional_token):
    criada = client.post(
        f"/consultas/{consulta_exemplo['id']}/respostas",
        json={"pergunta_id": pergunta_exemplo.id, "resposta_texto": "Texto original"},
        headers={"Authorization": f"Bearer {profissional_token}"},
    ).json()

    resposta = client.put(
        f"/consultas/{consulta_exemplo['id']}/respostas/{criada['id']}",
        json={"resposta_texto": "Texto corrigido"},
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["resposta_texto"] == "Texto corrigido"


def test_gerar_heredograma_com_mock_da_ia(
    client, consulta_exemplo, pergunta_exemplo, profissional_token, mocker, heredograma_exemplo
):
    client.post(
        f"/consultas/{consulta_exemplo['id']}/respostas",
        json={"pergunta_id": pergunta_exemplo.id, "resposta_texto": "Câncer de próstata no pai."},
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    mock_extrair = mocker.patch(
        "app.routes.consulta.extrair_heredograma",
        return_value=heredograma_exemplo,
    )

    resposta = client.post(
        f"/consultas/{consulta_exemplo['id']}/gerar-heredograma",
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 200
    mock_extrair.assert_called_once()

    corpo = resposta.json()
    assert corpo["consulta_id"] == consulta_exemplo["id"]

    codigos_retornados = {individuo["codigo"] for individuo in corpo["individuos"]}
    codigos_esperados = {individuo.codigo for individuo in heredograma_exemplo.individuos}
    assert codigos_retornados == codigos_esperados

    assert len(corpo["relacionamentos"]) == len(heredograma_exemplo.relacionamentos)


def test_gerar_heredograma_sem_respostas(client, consulta_exemplo, profissional_token, mocker):
    mock_extrair = mocker.patch("app.routes.consulta.extrair_heredograma")

    resposta = client.post(
        f"/consultas/{consulta_exemplo['id']}/gerar-heredograma",
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 400
    mock_extrair.assert_not_called()


def test_gerar_heredograma_acima_do_limite_retorna_429(
    client, consulta_exemplo, pergunta_exemplo, profissional_token, mocker, heredograma_exemplo
):
    """A rota é limitada a 60 requisições/minuto por IP (ver app/rate_limit.py)."""
    client.post(
        f"/consultas/{consulta_exemplo['id']}/respostas",
        json={"pergunta_id": pergunta_exemplo.id, "resposta_texto": "Câncer de próstata no pai."},
        headers={"Authorization": f"Bearer {profissional_token}"},
    )
    mocker.patch("app.routes.consulta.extrair_heredograma", return_value=heredograma_exemplo)

    ultima_resposta = None
    for _ in range(61):
        ultima_resposta = client.post(
            f"/consultas/{consulta_exemplo['id']}/gerar-heredograma",
            headers={"Authorization": f"Bearer {profissional_token}"},
        )

    assert ultima_resposta.status_code == 429
