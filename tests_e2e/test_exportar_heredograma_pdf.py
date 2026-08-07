from conftest import gerar_heredograma_de_teste


def test_exportar_pdf_inicia_download(pagina_logada_admin):
    """
    Não valida o CONTEÚDO do PDF gerado (jsPDF/svg2pdf.js rodam no
    navegador - isso precisa de inspeção visual manual, não dá para
    confirmar só por teste automatizado). Confirma apenas que clicar em
    "Exportar PDF" realmente dispara um download de um arquivo .pdf com
    nome não vazio - ou seja, que jsPDF/svg2pdf.js carregaram via CDN e
    `doc.svg()` + `doc.save()` rodaram sem lançar exceção.
    """
    page = pagina_logada_admin
    gerar_heredograma_de_teste(page)

    botao_exportar = page.locator("#btnExportarPdf")

    with page.expect_download() as info_download:
        botao_exportar.click()
    download = info_download.value

    nome_sugerido = download.suggested_filename
    assert nome_sugerido
    assert nome_sugerido.endswith(".pdf")
