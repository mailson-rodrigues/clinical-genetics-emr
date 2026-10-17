import re


def test_login_com_credenciais_validas_redireciona_para_index(page, login_admin):
    """
    Smoke test: validates the end-to-end E2E pipeline (real server +
    real database + real browser) through the simplest login
    flow of the system.
    """
    # domcontentloaded instead of the default "load" - see the note in conftest.py
    # (pagina_logada_admin) about why "load" is unstable in this environment.
    page.goto("/login.html", wait_until="domcontentloaded")

    page.fill("#email", login_admin["email"])
    page.fill("#senha", login_admin["senha"])
    page.click("button[type=submit]")

    page.wait_for_url(re.compile(r".*/index\.html$"))
    assert page.locator("#nomeUsuarioLogado").inner_text() == login_admin["nome"]


def test_login_com_senha_incorreta_mostra_erro(page, login_admin):
    # domcontentloaded instead of the default "load" - see the note in conftest.py
    # (pagina_logada_admin) about why "load" is unstable in this environment.
    page.goto("/login.html", wait_until="domcontentloaded")

    page.fill("#email", login_admin["email"])
    page.fill("#senha", "senha-errada")
    page.click("button[type=submit]")

    mensagem = page.locator("#mensagemLogin")
    mensagem.wait_for()
    assert "incorretos" in mensagem.inner_text().lower()
