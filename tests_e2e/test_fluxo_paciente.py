import re

from playwright.sync_api import expect

from conftest import gerar_cpf_unico


def test_cadastrar_buscar_editar_e_remover_paciente(pagina_logada_admin):
    page = pagina_logada_admin
    documento = gerar_cpf_unico()

    # -----------------------------------------------------------------
    # Registration (pacientes-cadastrar.html screen, full form)
    # -----------------------------------------------------------------
    # domcontentloaded instead of the default "load" - see the note in conftest.py
    # (pagina_logada_admin) about why "load" is unstable in this environment.
    page.goto("/pacientes-cadastrar.html", wait_until="domcontentloaded")

    page.fill("#nome", "Paciente E2E Completo")
    page.fill("#nomeSocial", "Apelido E2E")
    page.fill("#dataNascimento", "1990-05-15")
    page.select_option("#sexo", "F")
    page.select_option("#tipoSanguineo", "O+")
    page.fill("#documento", documento)
    page.fill("#rg", "1234567")
    page.fill("#telefone", "86999990000")
    page.fill("#whatsapp", "86999990000")
    page.fill("#email", "paciente.e2e@exemplo.com")
    page.fill("#cep", "64000-000")
    page.fill("#endereco", "Rua de Teste")
    page.fill("#numero", "100")
    page.fill("#complemento", "Apto 1")
    page.fill("#bairro", "Centro")
    page.fill("#cidade", "Teresina")
    page.select_option("#uf", "PI")
    page.check("#autorizacaoLgpd")

    page.click("#formPaciente button[type=submit]")

    mensagem = page.locator("#mensagemPaciente")
    mensagem.wait_for()
    assert "sucesso" in mensagem.inner_text().lower()

    # Registration automatically redirects to the search screen.
    page.wait_for_url(re.compile(r".*/pacientes\.html$"))

    # -----------------------------------------------------------------
    # Search (pacientes.html screen) - locates the newly created patient
    # by CPF, since the initial list only brings the most recent ones.
    # -----------------------------------------------------------------
    page.fill("#buscaPaciente", documento)
    linha_paciente = page.locator("#corpoTabelaPacientes tr", has_text=documento)
    linha_paciente.wait_for()
    assert linha_paciente.count() == 1

    # -----------------------------------------------------------------
    # Editing (opens pre-filled, changes the phone, saves)
    # -----------------------------------------------------------------
    linha_paciente.get_by_role("link", name="Editar").click()
    page.wait_for_url(re.compile(r".*/paciente-editar\.html\?paciente_id=\d+$"))

    # expect(...) automatically retries until the value matches (or the
    # timeout expires) - paciente-editar.js fills in the form via an
    # asynchronous fetch() after navigation, so checking input_value() directly (without
    # retry) may run before the filling finishes.
    expect(page.locator("#nome")).to_have_value("Paciente E2E Completo")
    expect(page.locator("#cidade")).to_have_value("Teresina")

    novo_telefone = "86988887777"
    page.fill("#telefone", "")
    page.fill("#telefone", novo_telefone)
    page.click("#formEditarPaciente button[type=submit]")

    mensagem_edicao = page.locator("#mensagemEdicao")
    mensagem_edicao.wait_for()
    assert "sucesso" in mensagem_edicao.inner_text().lower()

    # -----------------------------------------------------------------
    # Confirms persistence: goes back to the list (via the menu), searches
    # again and reopens the edit. Navigates by click ("Pacientes" link of the
    # menu), not by goto() - see the note in conftest.py
    # (pagina_logada_admin) about the instability of explicit
    # navigation calls in sequence in this environment.
    # -----------------------------------------------------------------
    page.get_by_role("link", name="Pacientes").click()
    page.wait_for_url(re.compile(r".*/pacientes\.html$"))

    page.fill("#buscaPaciente", documento)
    linha_paciente = page.locator("#corpoTabelaPacientes tr", has_text=documento)
    linha_paciente.wait_for()
    linha_paciente.get_by_role("link", name="Editar").click()
    page.wait_for_url(re.compile(r".*/paciente-editar\.html\?paciente_id=\d+$"))
    expect(page.locator("#telefone")).to_have_value(novo_telefone)

    # -----------------------------------------------------------------
    # Removal (soft delete) - native confirm() and alert() must be
    # accepted explicitly, otherwise Playwright dismisses them by default.
    # -----------------------------------------------------------------
    page.on("dialog", lambda dialog: dialog.accept())
    page.click("#btnRemoverPaciente")
    page.wait_for_url(re.compile(r".*/pacientes\.html$"))

    page.fill("#buscaPaciente", documento)
    corpo_tabela = page.locator("#corpoTabelaPacientes")
    expect(corpo_tabela).to_contain_text("Nenhum paciente encontrado")
