import re


def test_login_com_credenciais_validas_redireciona_para_index(page, login_admin):
    """
    Teste smoke: valida o pipeline E2E de ponta a ponta (servidor real +
    banco real + navegador real) através do fluxo de login mais simples
    do sistema.
    """
    # domcontentloaded em vez do padrão "load" - ver nota em conftest.py
    # (pagina_logada_admin) sobre por que "load" é instável neste ambiente.
    page.goto("/login.html", wait_until="domcontentloaded")

    page.fill("#email", login_admin["email"])
    page.fill("#senha", login_admin["senha"])
    page.click("button[type=submit]")

    page.wait_for_url(re.compile(r".*/index\.html$"))
    assert page.locator("#nomeUsuarioLogado").inner_text() == login_admin["nome"]


def test_login_com_senha_incorreta_mostra_erro(page, login_admin):
    # domcontentloaded em vez do padrão "load" - ver nota em conftest.py
    # (pagina_logada_admin) sobre por que "load" é instável neste ambiente.
    page.goto("/login.html", wait_until="domcontentloaded")

    page.fill("#email", login_admin["email"])
    page.fill("#senha", "senha-errada")
    page.click("button[type=submit]")

    mensagem = page.locator("#mensagemLogin")
    mensagem.wait_for()
    assert "incorretos" in mensagem.inner_text().lower()
