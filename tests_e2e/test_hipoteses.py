import json

from playwright.sync_api import expect

from conftest import gerar_heredograma_de_teste


def test_gerar_hipoteses_e_buscar_mais_fontes(pagina_logada_admin):
    """
    Mocka as chamadas de geração de hipóteses e de mais-fontes (nunca
    chega a chamar a IA de verdade - mesmo padrão de mock via
    page.route() já usado no teste do heredograma). Confirma o fluxo
    completo: gerar hipóteses, ver a fonte inicial, clicar em "Buscar
    mais fontes" e ver a nova fonte aparecer sem recarregar a página.
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

    # O aviso ético fica sempre visível, mesmo antes de gerar qualquer hipótese.
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

    # "Buscar mais fontes" - a nova fonte deve aparecer sem recarregar a página.
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
