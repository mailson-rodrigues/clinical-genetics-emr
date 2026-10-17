from conftest import gerar_heredograma_de_teste


def test_exportar_pdf_inicia_download(pagina_logada_admin):
    """
    Does not validate the CONTENT of the generated PDF (jsPDF/svg2pdf.js run in the
    browser - that needs manual visual inspection, it cannot be
    confirmed by an automated test alone). Only confirms that clicking
    "Exportar PDF" really triggers the download of a .pdf file with a
    non-empty name - that is, that jsPDF/svg2pdf.js loaded via CDN and
    `doc.svg()` + `doc.save()` ran without raising an exception.
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
