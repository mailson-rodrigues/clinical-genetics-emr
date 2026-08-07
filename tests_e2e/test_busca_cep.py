import json

from playwright.sync_api import expect


def test_busca_endereco_por_cep_preenche_campos(pagina_logada_admin):
    """
    A busca de endereço usa a API pública do ViaCEP (ver
    buscarEnderecoPorCep em enderecos.js) - mockada aqui via
    page.route() para o teste não depender dela estar no ar nem gastar
    uma chamada real. Confirma que, ao digitar um CEP de 8 dígitos em
    pacientes-cadastrar.html, os campos Endereço/Bairro/Cidade/UF são
    preenchidos a partir da resposta (fake) da API, e continuam
    editáveis depois.
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

    # domcontentloaded em vez do padrão "load" - ver nota em conftest.py
    # (pagina_logada_admin) sobre por que "load" é instável neste ambiente.
    page.goto("/pacientes-cadastrar.html", wait_until="domcontentloaded")

    page.fill("#cep", "64000000")

    expect(page.locator("#endereco")).to_have_value("Rua Fake de Teste")
    expect(page.locator("#bairro")).to_have_value("Bairro Fake")
    expect(page.locator("#cidade")).to_have_value("Teresina")
    expect(page.locator("#uf")).to_have_value("PI")

    # Os campos continuam editáveis depois do preenchimento automático -
    # não travamos nada (ver comentário em enderecos.js).
    page.fill("#endereco", "Rua Corrigida Manualmente")
    expect(page.locator("#endereco")).to_have_value("Rua Corrigida Manualmente")


def test_busca_endereco_por_cep_nao_encontrado_mostra_aviso_discreto(pagina_logada_admin):
    """
    CEP inexistente: a API real do ViaCEP responde 200 com
    {"erro": true} (sem lançar HTTP de erro) - mockamos esse mesmo
    formato. O formulário não deve travar nem mostrar popup - só um
    aviso discreto ao lado do campo CEP.
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
