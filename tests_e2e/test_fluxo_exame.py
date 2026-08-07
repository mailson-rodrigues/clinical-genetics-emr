import re

from conftest import (
    CONDICAO_TESTE_ENCAMINHAMENTO_EXAME,
    criar_consulta_de_teste_encaminhamento_exame,
    voltar_para_consultas_do_paciente,
)


def test_registrar_exame_e_persistir_status(pagina_logada_admin):
    page = pagina_logada_admin
    documento = criar_consulta_de_teste_encaminhamento_exame(page)

    linha_consulta = page.locator("#corpoTabelaConsultas tr", has_text=CONDICAO_TESTE_ENCAMINHAMENTO_EXAME)
    linha_consulta.get_by_role("link", name="Exames").click()
    page.wait_for_url(re.compile(r".*/exames\.html\?consulta_id=\d+$"))

    # Não geramos heredograma real nesta consulta, então o select de
    # indivíduo fica desabilitado - o exame é registrado sem vínculo,
    # como "paciente/consulta geral" (comportamento coberto por
    # tests/test_exames.py::test_criar_exame_sem_vincular_individuo).
    page.fill("#tipoExame", "Painel BRCA1/BRCA2")
    page.click("#formExame button[type=submit]")

    mensagem = page.locator("#mensagemExame")
    mensagem.wait_for()
    assert "sucesso" in mensagem.inner_text().lower()

    linha = page.locator("#corpoTabelaExames tr", has_text="BRCA1/BRCA2")
    linha.wait_for()
    assert "Paciente/consulta geral" in linha.inner_text()
    linha.locator("select.select-status").select_option("concluido")
    page.wait_for_timeout(300)

    voltar_para_consultas_do_paciente(page, documento)
    linha_consulta = page.locator("#corpoTabelaConsultas tr", has_text=CONDICAO_TESTE_ENCAMINHAMENTO_EXAME)
    linha_consulta.get_by_role("link", name="Exames").click()
    page.wait_for_url(re.compile(r".*/exames\.html\?consulta_id=\d+$"))

    linha = page.locator("#corpoTabelaExames tr", has_text="BRCA1/BRCA2")
    linha.wait_for()
    assert linha.locator("select.select-status").input_value() == "concluido"
