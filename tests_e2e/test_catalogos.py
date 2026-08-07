import uuid


def test_cadastrar_cid_e_operadora_pela_tela(pagina_logada_admin):
    page = pagina_logada_admin
    # domcontentloaded em vez do padrão "load" - ver nota em conftest.py
    # (pagina_logada_admin) sobre por que "load" é instável neste ambiente.
    page.goto("/catalogos.html", wait_until="domcontentloaded")

    sufixo = uuid.uuid4().hex[:8]

    # -----------------------------------------------------------------
    # CID
    # -----------------------------------------------------------------
    codigo_cid = f"Z{sufixo[:2].upper()}"
    descricao_cid = f"Descrição de teste E2E {sufixo}"

    page.fill("#codigoCid", codigo_cid)
    page.fill("#descricaoCid", descricao_cid)
    page.fill("#capituloCid", "Capítulo de teste")
    page.click("#formCid button[type=submit]")

    mensagem_cid = page.locator("#mensagemCid")
    mensagem_cid.wait_for()
    assert "sucesso" in mensagem_cid.inner_text().lower()

    linha_cid = page.locator("#corpoTabelaCid tr", has_text=codigo_cid)
    linha_cid.wait_for()
    assert linha_cid.count() == 1

    # -----------------------------------------------------------------
    # Operadora
    # -----------------------------------------------------------------
    nome_operadora = f"Operadora Teste E2E {sufixo}"

    page.fill("#nomeOperadora", nome_operadora)
    page.click("#formOperadora button[type=submit]")

    mensagem_operadora = page.locator("#mensagemOperadora")
    mensagem_operadora.wait_for()
    assert "sucesso" in mensagem_operadora.inner_text().lower()

    linha_operadora = page.locator("#corpoTabelaOperadora tr", has_text=nome_operadora)
    linha_operadora.wait_for()
    assert linha_operadora.count() == 1
