from playwright.sync_api import expect


def test_dashboard_mostra_indicadores_apos_login(pagina_logada_admin):
    """
    Confirms that the home page (dashboard) renders the 4 indicator cards
    with real numbers (not stuck on the initial "-", nor "undefined"/"NaN")
    after GET /dashboard/resumo. Does not validate
    the exact values - only that the structure loads without errors.
    """
    page = pagina_logada_admin

    ids_cards = [
        "numPacientesAtivos",
        "numConsultasMes",
        "numEncaminhamentosPendentes",
        "numExamesAguardando",
    ]

    for id_card in ids_cards:
        elemento = page.locator(f"#{id_card}")
        expect(elemento).not_to_have_text("-")
        texto = elemento.inner_text().strip()
        assert texto.isdigit(), f"#{id_card} não é um número: {texto!r}"

    expect(page.locator("#listaAtividadeRecente")).not_to_contain_text("Erro:")
