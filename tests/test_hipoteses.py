from app.schemas.hipotese import HipotesesExtraidas, HipoteseDiagnosticaExtraida, FonteHipoteseExtraida


def _hipoteses_exemplo():
    return HipotesesExtraidas(hipoteses=[
        HipoteseDiagnosticaExtraida(
            condicao="Síndrome de Li-Fraumeni",
            justificativa=(
                "Múltiplos cânceres em idade precoce na família, padrão "
                "compatível com mutação germinativa em TP53."
            ),
            cid_sugerido="C97",
            fontes=[
                FonteHipoteseExtraida(
                    titulo="Li-Fraumeni Syndrome",
                    url="https://omim.org/entry/151623",
                    origem="OMIM",
                ),
                FonteHipoteseExtraida(
                    titulo="Li-Fraumeni syndrome overview",
                    url="https://rarediseases.info.nih.gov/diseases/7218/li-fraumeni-syndrome",
                    origem="GARD/NIH",
                ),
            ],
        ),
    ])


def _registrar_resposta(client, consulta_id, pergunta_id, token):
    client.post(
        f"/consultas/{consulta_id}/respostas",
        json={"pergunta_id": pergunta_id, "resposta_texto": "Câncer e sarcoma na família antes dos 40 anos."},
        headers={"Authorization": f"Bearer {token}"},
    )


def test_gerar_hipoteses_com_mock_da_ia(client, consulta_exemplo, pergunta_exemplo, profissional_token, mocker):
    _registrar_resposta(client, consulta_exemplo["id"], pergunta_exemplo.id, profissional_token)

    mock_gerar = mocker.patch("app.routes.hipotese.gerar_hipoteses", return_value=_hipoteses_exemplo())

    resposta = client.post(
        f"/consultas/{consulta_exemplo['id']}/hipoteses",
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 201
    mock_gerar.assert_called_once()

    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["condicao"] == "Síndrome de Li-Fraumeni"
    assert corpo[0]["consulta_id"] == consulta_exemplo["id"]
    assert corpo[0]["cid_sugerido"] == "C97"
    assert corpo[0]["ordem"] == 1
    assert len(corpo[0]["fontes"]) == 2
    assert corpo[0]["fontes"][0]["origem"] == "OMIM"


def test_gerar_hipoteses_define_ordem_pela_posicao_da_resposta_da_ia(
    client, consulta_exemplo, pergunta_exemplo, profissional_token, mocker
):
    """
    "ordem" não é um campo pedido à IA - é derivado da posição em que
    cada hipótese vem na lista (a IA já é instruída a ordenar da mais
    para a menos provável, ver PROMPT_SISTEMA_HIPOTESES).
    """
    hipoteses = HipotesesExtraidas(hipoteses=[
        HipoteseDiagnosticaExtraida(condicao="Mais provável", justificativa="Justificativa A.", fontes=[]),
        HipoteseDiagnosticaExtraida(condicao="Menos provável", justificativa="Justificativa B.", fontes=[]),
    ])
    _registrar_resposta(client, consulta_exemplo["id"], pergunta_exemplo.id, profissional_token)
    mocker.patch("app.routes.hipotese.gerar_hipoteses", return_value=hipoteses)

    resposta = client.post(
        f"/consultas/{consulta_exemplo['id']}/hipoteses",
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    corpo = resposta.json()
    assert corpo[0]["condicao"] == "Mais provável"
    assert corpo[0]["ordem"] == 1
    assert corpo[0]["cid_sugerido"] is None
    assert corpo[1]["condicao"] == "Menos provável"
    assert corpo[1]["ordem"] == 2

    # GET também devolve na mesma ordem (ORDER BY ordem no backend)
    resposta_get = client.get(f"/consultas/{consulta_exemplo['id']}/hipoteses")
    corpo_get = resposta_get.json()
    assert [h["condicao"] for h in corpo_get] == ["Mais provável", "Menos provável"]


def test_gerar_hipoteses_sem_respostas(client, consulta_exemplo, profissional_token, mocker):
    mock_gerar = mocker.patch("app.routes.hipotese.gerar_hipoteses")

    resposta = client.post(
        f"/consultas/{consulta_exemplo['id']}/hipoteses",
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 400
    mock_gerar.assert_not_called()


def test_gerar_hipoteses_limita_a_5_fontes_por_hipotese(
    client, consulta_exemplo, pergunta_exemplo, profissional_token, mocker
):
    muitas_fontes = [
        FonteHipoteseExtraida(titulo=f"Fonte {i}", url=f"https://omim.org/entry/{i}", origem="OMIM")
        for i in range(8)
    ]
    hipoteses = HipotesesExtraidas(hipoteses=[
        HipoteseDiagnosticaExtraida(condicao="Condição Teste", justificativa="Justificativa teste.", fontes=muitas_fontes)
    ])
    _registrar_resposta(client, consulta_exemplo["id"], pergunta_exemplo.id, profissional_token)
    mocker.patch("app.routes.hipotese.gerar_hipoteses", return_value=hipoteses)

    resposta = client.post(
        f"/consultas/{consulta_exemplo['id']}/hipoteses",
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 201
    assert len(resposta.json()[0]["fontes"]) == 5


def test_listar_hipoteses(client, consulta_exemplo, pergunta_exemplo, profissional_token, mocker):
    _registrar_resposta(client, consulta_exemplo["id"], pergunta_exemplo.id, profissional_token)
    mocker.patch("app.routes.hipotese.gerar_hipoteses", return_value=_hipoteses_exemplo())
    client.post(
        f"/consultas/{consulta_exemplo['id']}/hipoteses",
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    resposta = client.get(f"/consultas/{consulta_exemplo['id']}/hipoteses")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


def test_buscar_mais_fontes_anexa_sem_substituir(
    client, consulta_exemplo, pergunta_exemplo, profissional_token, mocker
):
    _registrar_resposta(client, consulta_exemplo["id"], pergunta_exemplo.id, profissional_token)
    mocker.patch("app.routes.hipotese.gerar_hipoteses", return_value=_hipoteses_exemplo())
    hipotese_criada = client.post(
        f"/consultas/{consulta_exemplo['id']}/hipoteses",
        headers={"Authorization": f"Bearer {profissional_token}"},
    ).json()[0]

    novas_fontes = [
        FonteHipoteseExtraida(
            titulo="Nova fonte", url="https://pubmed.ncbi.nlm.nih.gov/12345", origem="PubMed"
        ),
    ]
    mock_mais_fontes = mocker.patch("app.routes.hipotese.buscar_mais_fontes", return_value=novas_fontes)

    resposta = client.post(
        f"/consultas/{consulta_exemplo['id']}/hipoteses/{hipotese_criada['id']}/mais-fontes",
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 200
    mock_mais_fontes.assert_called_once()
    corpo = resposta.json()
    # 2 fontes originais + 1 nova = 3, sem substituir as existentes
    assert len(corpo["fontes"]) == 3
    urls = {fonte["url"] for fonte in corpo["fontes"]}
    assert "https://pubmed.ncbi.nlm.nih.gov/12345" in urls
    assert "https://omim.org/entry/151623" in urls


def test_mais_fontes_hipotese_inexistente(client, consulta_exemplo, profissional_token, mocker):
    mock_mais_fontes = mocker.patch("app.routes.hipotese.buscar_mais_fontes")

    resposta = client.post(
        f"/consultas/{consulta_exemplo['id']}/hipoteses/9999/mais-fontes",
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 404
    mock_mais_fontes.assert_not_called()


def test_gerar_hipoteses_sem_login(client, consulta_exemplo):
    resposta = client.post(f"/consultas/{consulta_exemplo['id']}/hipoteses")
    assert resposta.status_code == 401


def test_gerar_hipoteses_acima_do_limite_retorna_429(
    client, consulta_exemplo, pergunta_exemplo, profissional_token, mocker
):
    """A rota é limitada a 20 requisições/minuto por IP (ver app/routes/hipotese.py)."""
    _registrar_resposta(client, consulta_exemplo["id"], pergunta_exemplo.id, profissional_token)
    mocker.patch("app.routes.hipotese.gerar_hipoteses", return_value=_hipoteses_exemplo())

    ultima_resposta = None
    for _ in range(21):
        ultima_resposta = client.post(
            f"/consultas/{consulta_exemplo['id']}/hipoteses",
            headers={"Authorization": f"Bearer {profissional_token}"},
        )

    assert ultima_resposta.status_code == 429
