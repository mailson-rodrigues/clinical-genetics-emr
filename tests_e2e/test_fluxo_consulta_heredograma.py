from conftest import gerar_heredograma_de_teste


def test_gerar_heredograma_e_visualizar_svg(pagina_logada_admin):
    """
    Fluxo completo: cadastro de paciente + consulta, responde perguntas
    do roteiro, gera o heredograma (com a chamada à IA mockada - ver
    gerar_heredograma_de_teste em conftest.py) e confirma que o SVG foi
    renderizado na tela de heredograma.
    """
    page = pagina_logada_admin
    gerar_heredograma_de_teste(page)

    svg = page.locator("#heredogramaContainer svg")
    assert svg.count() == 1
