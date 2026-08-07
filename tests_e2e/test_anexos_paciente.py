import re

from playwright.sync_api import expect

from conftest import cadastrar_paciente_via_ui


def test_upload_anexo_paciente_aparece_na_lista(pagina_logada_admin):
    """
    Fluxo de upload de documentos anexados na tela de edição de
    paciente: envia um arquivo mínimo (buffer em memória via
    set_input_files, sem precisar de um arquivo fixture em disco) e
    confirma que ele aparece na lista logo depois.
    """
    page = pagina_logada_admin

    documento = cadastrar_paciente_via_ui(page, "Paciente Anexo E2E", "1985-06-15", "F")

    page.fill("#buscaPaciente", documento)
    linha_paciente = page.locator("#corpoTabelaPacientes tr", has_text=documento)
    linha_paciente.wait_for()
    linha_paciente.get_by_role("link", name="Editar").click()
    page.wait_for_url(re.compile(r".*/paciente-editar\.html\?paciente_id=\d+$"))

    expect(page.locator("#anexosContainer")).to_be_visible()

    page.set_input_files(
        "#arquivoAnexoPaciente",
        {
            "name": "laudo-teste.pdf",
            "mimeType": "application/pdf",
            "buffer": b"%PDF-1.4 conteudo minimo de teste",
        },
    )
    page.click("#formAnexoPaciente button[type=submit]")

    mensagem = page.locator("#mensagemAnexoPaciente")
    mensagem.wait_for()
    assert "sucesso" in mensagem.inner_text().lower()

    item_anexo = page.locator("#listaAnexosPaciente .item-anexo", has_text="laudo-teste.pdf")
    item_anexo.wait_for()
    assert item_anexo.count() == 1
