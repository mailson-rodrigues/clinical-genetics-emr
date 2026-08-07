import re

from playwright.sync_api import expect

from conftest import gerar_cpf_unico


def test_cadastrar_buscar_editar_e_remover_paciente(pagina_logada_admin):
    page = pagina_logada_admin
    documento = gerar_cpf_unico()

    # -----------------------------------------------------------------
    # Cadastro (tela pacientes-cadastrar.html, formulário completo)
    # -----------------------------------------------------------------
    # domcontentloaded em vez do padrão "load" - ver nota em conftest.py
    # (pagina_logada_admin) sobre por que "load" é instável neste ambiente.
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

    # O cadastro redireciona automaticamente para a tela de busca.
    page.wait_for_url(re.compile(r".*/pacientes\.html$"))

    # -----------------------------------------------------------------
    # Busca (tela pacientes.html) - localiza o paciente recém-criado
    # pelo CPF, já que a lista inicial só traz os mais recentes.
    # -----------------------------------------------------------------
    page.fill("#buscaPaciente", documento)
    linha_paciente = page.locator("#corpoTabelaPacientes tr", has_text=documento)
    linha_paciente.wait_for()
    assert linha_paciente.count() == 1

    # -----------------------------------------------------------------
    # Edição (abre preenchido, altera telefone, salva)
    # -----------------------------------------------------------------
    linha_paciente.get_by_role("link", name="Editar").click()
    page.wait_for_url(re.compile(r".*/paciente-editar\.html\?paciente_id=\d+$"))

    # expect(...) re-tenta automaticamente até o valor bater (ou expirar o
    # timeout) - paciente-editar.js preenche o formulário via fetch()
    # assíncrono após a navegação, então checar input_value() direto (sem
    # retry) pode rodar antes do preenchimento terminar.
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
    # Confirma persistência: volta para a lista (via menu), busca de
    # novo e reabre a edição. Navega por clique (link "Pacientes" do
    # menu), não por goto() - ver nota em conftest.py
    # (pagina_logada_admin) sobre instabilidade de chamadas explícitas
    # de navegação em sequência neste ambiente.
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
    # Remoção (soft delete) - confirm() e alert() nativos precisam ser
    # aceitos explicitamente, senão o Playwright os dispensa por padrão.
    # -----------------------------------------------------------------
    page.on("dialog", lambda dialog: dialog.accept())
    page.click("#btnRemoverPaciente")
    page.wait_for_url(re.compile(r".*/pacientes\.html$"))

    page.fill("#buscaPaciente", documento)
    corpo_tabela = page.locator("#corpoTabelaPacientes")
    expect(corpo_tabela).to_contain_text("Nenhum paciente encontrado")
