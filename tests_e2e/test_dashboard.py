from playwright.sync_api import expect


def test_dashboard_mostra_indicadores_apos_login(pagina_logada_admin):
    """
    Confirma que a página inicial (dashboard) renderiza os 4 cards de
    indicadores com números de verdade (não travados no "-" inicial,
    nem "undefined"/"NaN") depois do GET /dashboard/resumo. Não valida
    os valores exatos - só que a estrutura carrega sem erro.
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
