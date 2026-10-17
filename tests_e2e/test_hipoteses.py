import json

from playwright.sync_api import expect

from conftest import gerar_heredograma_de_teste


def test_gerar_hipoteses_e_buscar_mais_fontes(pagina_logada_admin):
    """
    Mocks the hypothesis-generation and more-sources calls (it never
    actually calls the AI - same mock pattern via
    page.route() already used in the pedigree test). Confirms the full
    flow: generate hypotheses, see the initial source, click "Buscar
    mais fontes" and see the new source appear without reloading the page.
    """
    page = pagina_logada_admin
    consulta_id = gerar_heredograma_de_teste(page)

    hipotese_fake = {
        "id": 1,
        "consulta_id": int(consulta_id),
        "condicao": "Síndrome de Li-Fraumeni",
        "justificativa": "Múltiplos cânceres em idade precoce na família.",
        "cid_sugerido": "C97",
        "ordem": 1,
        "criado_em": "2026-01-01T00:00:00",
        "fontes": [
            {
                "id": 1,
                "titulo": "Li-Fraumeni Syndrome",
                "url": "https://omim.org/entry/151623",
                "origem": "OMIM",
            },
        ],
    }

    def _responder_hipoteses(route):
        route.fulfill(
            status=201 if route.request.method == "POST" else 200,
            content_type="application/json",
            body=json.dumps([hipotese_fake]),
        )

    page.route(f"**/consultas/{consulta_id}/hipoteses", _responder_hipoteses)

    page.goto(f"/hipoteses.html?consulta_id={consulta_id}", wait_until="domcontentloaded")

    # The ethical notice is always visible, even before generating any hypothesis.
    expect(page.locator(".aviso-etico")).to_contain_text("não é um diagnóstico")

    page.click("#btnGerarHipoteses")

    mensagem = page.locator("#mensagemGeracao")
    mensagem.wait_for()
    expect(mensagem).to_have_text("Hipóteses geradas com sucesso!")

    page.locator("#listaHipoteses h3", has_text="Síndrome de Li-Fraumeni").wait_for()

    cid_exibido = page.locator("#listaHipoteses h3 .codigo-clinico", has_text="C97")
    expect(cid_exibido).to_be_visible()

    link_fonte = page.locator("#fontesHipotese1 a", has_text="Li-Fraumeni Syndrome")
    expect(link_fonte).to_have_attribute("href", "https://omim.org/entry/151623")

    # "Buscar mais fontes" - the new source must appear without reloading the page.
    hipotese_com_mais_fontes = dict(hipotese_fake)
    hipotese_com_mais_fontes["fontes"] = hipotese_fake["fontes"] + [
        {"id": 2, "titulo": "Nova fonte", "url": "https://pubmed.ncbi.nlm.nih.gov/999", "origem": "PubMed"},
    ]

    page.route(
        f"**/consultas/{consulta_id}/hipoteses/1/mais-fontes",
        lambda route: route.fulfill(
            status=200, content_type="application/json", body=json.dumps(hipotese_com_mais_fontes)
        ),
    )

    page.click("[data-mais-fontes='1']")

    page.locator("#fontesHipotese1 a", has_text="Nova fonte").wait_for()
    expect(page.locator("#fontesHipotese1 li")).to_have_count(2)
