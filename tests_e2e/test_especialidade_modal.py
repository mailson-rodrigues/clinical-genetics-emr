import uuid

from playwright.sync_api import expect


def test_cadastrar_especialidade_pelo_modal(pagina_logada_admin):
    """
    Testa o botão "+" ao lado do <select> de especialidade em
    profissionais.html: abre o modal (<dialog>), cadastra uma
    especialidade nova (POST /especialidades/) e confirma que ela
    aparece já selecionada no formulário, sem precisar recarregar a
    página manualmente.
    """
    page = pagina_logada_admin
    # domcontentloaded em vez do padrão "load" - ver nota em conftest.py
    # (pagina_logada_admin) sobre por que "load" é instável neste ambiente.
    page.goto("/profissionais.html", wait_until="domcontentloaded")

    nome_especialidade = f"Especialidade E2E {uuid.uuid4().hex[:8]}"

    page.click("#btnNovaEspecialidade")
    expect(page.locator("#modalEspecialidade")).to_be_visible()

    page.fill("#nomeNovaEspecialidade", nome_especialidade)
    page.click("#formNovaEspecialidade button[type=submit]")

    expect(page.locator("#modalEspecialidade")).to_be_hidden()

    valor_selecionado = page.locator("#especialidade").input_value()
    texto_opcao_selecionada = page.locator(
        f"#especialidade option[value='{valor_selecionado}']"
    ).inner_text()
    assert texto_opcao_selecionada == nome_especialidade
