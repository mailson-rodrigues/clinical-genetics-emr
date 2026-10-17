from conftest import gerar_heredograma_de_teste


def test_gerar_heredograma_e_visualizar_svg(pagina_logada_admin):
    """
    Full flow: patient + consultation registration, answers questions
    of the script, generates the pedigree (with the AI call mocked - see
    gerar_heredograma_de_teste in conftest.py) and confirms that the SVG was
    rendered on the pedigree screen.
    """
    page = pagina_logada_admin
    gerar_heredograma_de_teste(page)

    svg = page.locator("#heredogramaContainer svg")
    assert svg.count() == 1
