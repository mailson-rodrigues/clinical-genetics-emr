from conftest import gerar_heredograma_de_teste


def test_exportar_png_inicia_download(pagina_logada_admin):
    """
    Não valida o CONTEÚDO da imagem gerada (o SVG é rasterizado num
    <canvas> e exportado via toBlob - isso precisa de inspeção visual
    manual, não dá para confirmar só por teste automatizado). Confirma
    apenas que clicar em "Exportar Imagem (PNG)" realmente dispara um
    download de um arquivo .png com nome não vazio - ou seja, que
    carregarImagemSVG + canvas.drawImage + toBlob rodaram sem lançar
    exceção.
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
