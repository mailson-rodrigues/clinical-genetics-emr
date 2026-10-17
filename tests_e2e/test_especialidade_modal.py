import uuid

from playwright.sync_api import expect


def test_cadastrar_especialidade_pelo_modal(pagina_logada_admin):
    """
    Tests the "+" button next to the specialty <select> in
    profissionais.html: opens the modal (<dialog>), registers a new
    specialty (POST /especialidades/) and confirms that it
    appears already selected in the form, without needing to reload the
    page manually.
    """
    page = pagina_logada_admin
    # domcontentloaded instead of the default "load" - see the note in conftest.py
    # (pagina_logada_admin) about why "load" is unstable in this environment.
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
