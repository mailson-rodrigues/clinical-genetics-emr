from conftest import gerar_heredograma_de_teste


def test_exportar_png_inicia_download(pagina_logada_admin):
    """
    Does not validate the CONTENT of the generated image (the SVG is rasterized into a
    <canvas> and exported via toBlob - that needs manual visual
    inspection, it cannot be confirmed by an automated test alone). Only
    confirms that clicking "Exportar Imagem (PNG)" really triggers the
    download of a .png file with a non-empty name - that is, that
    carregarImagemSVG + canvas.drawImage + toBlob ran without raising an
    exception.
    """
    page = pagina_logada_admin
    gerar_heredograma_de_teste(page)

    botao_exportar = page.locator("#btnExportarPng")

    with page.expect_download() as info_download:
        botao_exportar.click()
    download = info_download.value

    nome_sugerido = download.suggested_filename
    assert nome_sugerido
    assert nome_sugerido.endswith(".png")
