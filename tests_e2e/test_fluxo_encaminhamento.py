import re

from conftest import (
    CONDICAO_TESTE_ENCAMINHAMENTO_EXAME,
    criar_consulta_de_teste_encaminhamento_exame,
    voltar_para_consultas_do_paciente,
)


def test_registrar_encaminhamento_e_persistir_status(pagina_logada_admin):
    page = pagina_logada_admin
    documento = criar_consulta_de_teste_encaminhamento_exame(page)

    linha_consulta = page.locator("#corpoTabelaConsultas tr", has_text=CONDICAO_TESTE_ENCAMINHAMENTO_EXAME)
    linha_consulta.get_by_role("link", name="Encaminhamentos").click()
    page.wait_for_url(re.compile(r".*/encaminhamentos\.html\?consulta_id=\d+$"))

    page.fill("#motivo", "Achados sugerem risco elevado - encaminhar para oncogenética.")
    page.click("#formEncaminhamento button[type=submit]")

    mensagem = page.locator("#mensagemEncaminhamento")
    mensagem.wait_for()
    assert "sucesso" in mensagem.inner_text().lower()

    linha = page.locator("#corpoTabelaEncaminhamentos tr", has_text="oncogenética")
    linha.wait_for()
    linha.locator("select.select-status").select_option("concluido")
    # select_option dispara o PUT em segundo plano (evento "change") e
    # retorna na hora - uma pequena espera garante que o PUT já chegou ao
    # backend antes de navegarmos para longe da página.
    page.wait_for_timeout(300)

    # Confirma que o status persistiu no backend - navega (por cliques) de
    # volta até a mesma tela e confere o valor, em vez de usar reload().
    voltar_para_consultas_do_paciente(page, documento)
    linha_consulta = page.locator("#corpoTabelaConsultas tr", has_text=CONDICAO_TESTE_ENCAMINHAMENTO_EXAME)
    linha_consulta.get_by_role("link", name="Encaminhamentos").click()
    page.wait_for_url(re.compile(r".*/encaminhamentos\.html\?consulta_id=\d+$"))

    linha = page.locator("#corpoTabelaEncaminhamentos tr", has_text="oncogenética")
    linha.wait_for()
    assert linha.locator("select.select-status").input_value() == "concluido"
