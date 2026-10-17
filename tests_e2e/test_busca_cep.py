import json

from playwright.sync_api import expect


def test_busca_endereco_por_cep_preenche_campos(pagina_logada_admin):
    """
    The address lookup uses the public ViaCEP API (see
    buscarEnderecoPorCep in enderecos.js) - mocked here via
    page.route() so the test does not depend on it being up nor spend
    a real call. Confirms that, when typing an 8-digit CEP in
    pacientes-cadastrar.html, the Endereço/Bairro/Cidade/UF fields are
    filled from the (fake) API response, and remain
    editable afterwards.
    """
    page = pagina_logada_admin

    endereco_fake = {
        "cep": "64000-000",
        "logradouro": "Rua Fake de Teste",
        "bairro": "Bairro Fake",
        "localidade": "Teresina",
        "uf": "PI",
    }

    def responder_com_endereco_fake(route):
        route.fulfill(status=200, content_type="application/json", body=json.dumps(endereco_fake))

    page.route("https://viacep.com.br/ws/**", responder_com_endereco_fake)

    # domcontentloaded instead of the default "load" - see the note in conftest.py
    # (pagina_logada_admin) about why "load" is unstable in this environment.
    page.goto("/pacientes-cadastrar.html", wait_until="domcontentloaded")

    page.fill("#cep", "64000000")

    expect(page.locator("#endereco")).to_have_value("Rua Fake de Teste")
    expect(page.locator("#bairro")).to_have_value("Bairro Fake")
    expect(page.locator("#cidade")).to_have_value("Teresina")
    expect(page.locator("#uf")).to_have_value("PI")

    # The fields remain editable after the automatic filling -
    # we do not lock anything (see the comment in enderecos.js).
    page.fill("#endereco", "Rua Corrigida Manualmente")
    expect(page.locator("#endereco")).to_have_value("Rua Corrigida Manualmente")


def test_busca_endereco_por_cep_nao_encontrado_mostra_aviso_discreto(pagina_logada_admin):
    """
    Nonexistent CEP: the real ViaCEP API answers 200 with
    {"erro": true} (without raising an HTTP error) - we mock that same
    format. The form must not freeze nor show a popup - only a
    discreet notice next to the CEP field.
    """
    page = pagina_logada_admin

    def responder_cep_nao_encontrado(route):
        route.fulfill(status=200, content_type="application/json", body=json.dumps({"erro": True}))

    page.route("https://viacep.com.br/ws/**", responder_cep_nao_encontrado)

    page.goto("/pacientes-cadastrar.html", wait_until="domcontentloaded")
    page.fill("#cep", "99999999")

    mensagem = page.locator("#mensagemCep")
    expect(mensagem).to_have_text("CEP não encontrado, preencha manualmente.")
    expect(page.locator("#endereco")).to_have_value("")
