import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest
import requests

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_BANCO_E2E = RAIZ_PROJETO / "test_e2e.db"
CAMINHO_UPLOADS_E2E = RAIZ_PROJETO / "test_uploads_e2e"

# Banco SQLite isolado, exclusivo dos testes E2E - nunca o heredograma.db
# real (dev) nem o test_heredograma.db usado pelos testes de backend em
# tests/ (que rodam em processo, sem subir servidor de verdade).
DATABASE_URL_E2E = f"sqlite:///{CAMINHO_BANCO_E2E.as_posix()}"

PORTA_SERVIDOR_E2E = 8001
URL_BASE_E2E = f"http://127.0.0.1:{PORTA_SERVIDOR_E2E}"


def _remover_banco_e2e():
    """
    No Windows, o SO pode levar um instante para liberar o handle do
    arquivo SQLite depois que o processo do uvicorn é terminado - tenta
    algumas vezes antes de desistir, em vez de falhar o teardown.
    """
    if not CAMINHO_BANCO_E2E.exists():
        return
    for tentativa in range(10):
        try:
            CAMINHO_BANCO_E2E.unlink()
            return
        except PermissionError:
            if tentativa == 9:
                raise
            time.sleep(0.3)


def _aguardar_servidor_pronto(processo, timeout=30):
    """Faz polling em /api/status até o servidor responder, ou falha com um erro claro."""
    prazo_final = time.time() + timeout
    while time.time() < prazo_final:
        if processo.poll() is not None:
            saida = processo.stdout.read() if processo.stdout else ""
            raise RuntimeError(
                f"O servidor E2E (uvicorn) encerrou prematuramente antes de ficar pronto.\n"
                f"Saída do processo:\n{saida}"
            )
        try:
            resposta = requests.get(f"{URL_BASE_E2E}/api/status", timeout=1)
            if resposta.status_code == 200:
                return
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(0.5)

    processo.terminate()
    raise RuntimeError(f"O servidor E2E não respondeu em {URL_BASE_E2E}/api/status após {timeout}s.")


@pytest.fixture(scope="session", autouse=True)
def servidor_e2e():
    """
    Sobe a aplicação real (uvicorn) num processo separado, num banco
    SQLite temporário e isolado, para os testes E2E (Playwright)
    exercitarem o sistema de ponta a ponta com um único comando - sem
    precisar de nenhum terminal manual, servidor já rodando, ou banco
    pré-existente.
    """
    _remover_banco_e2e()
    shutil.rmtree(CAMINHO_UPLOADS_E2E, ignore_errors=True)

    env = os.environ.copy()
    env["DATABASE_URL"] = DATABASE_URL_E2E
    env["UPLOAD_DIR"] = str(CAMINHO_UPLOADS_E2E)

    resultado_migracao = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=RAIZ_PROJETO,
        env=env,
        capture_output=True,
        text=True,
    )
    if resultado_migracao.returncode != 0:
        raise RuntimeError(
            "Falha ao rodar as migrações do Alembic no banco E2E.\n"
            f"stdout:\n{resultado_migracao.stdout}\nstderr:\n{resultado_migracao.stderr}"
        )

    # As migrações só criam o schema (tabelas vazias) - o roteiro de
    # anamnese é populado à parte (mesmo processo usado em produção, ver
    # seed_perguntas.py), necessário para os testes de fluxo de
    # anamnese/heredograma terem perguntas reais para responder na UI.
    resultado_seed = subprocess.run(
        [sys.executable, "seed_perguntas.py"],
        cwd=RAIZ_PROJETO,
        env=env,
        capture_output=True,
        text=True,
    )
    if resultado_seed.returncode != 0:
        raise RuntimeError(
            "Falha ao popular o roteiro de perguntas no banco E2E.\n"
            f"stdout:\n{resultado_seed.stdout}\nstderr:\n{resultado_seed.stderr}"
        )

    processo = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--port", str(PORTA_SERVIDOR_E2E),
            # O padrão do uvicorn é fechar conexões keep-alive ociosas após
            # só 5s. Testes de UI têm pausas reais entre ações (preencher
            # campos, esperar elementos) que podem passar disso - quando o
            # navegador tenta reaproveitar uma conexão que o servidor
            # acabou de fechar por inatividade, a requisição fica
            # pendurada até o timeout do Playwright (era exatamente esse
            # o sintoma: page.goto/reload/wait_for_url travando sempre a
            # partir do 2º teste da sessão, nunca reproduzível via chamadas
            # HTTP puras - só via navegador real, com pausas reais).
            "--timeout-keep-alive", "120",
        ],
        cwd=RAIZ_PROJETO,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        _aguardar_servidor_pronto(processo)
        yield
    finally:
        processo.terminate()
        try:
            processo.wait(timeout=10)
        except subprocess.TimeoutExpired:
            processo.kill()
        _remover_banco_e2e()
        shutil.rmtree(CAMINHO_UPLOADS_E2E, ignore_errors=True)


@pytest.fixture(scope="session")
def base_url():
    """
    Sobrescreve o fixture `base_url` do pytest-playwright: em vez de
    depender da flag de linha de comando --base-url, aponta sempre para
    o servidor E2E local (porta 8001, diferente da 8000 do servidor de
    desenvolvimento, para não haver conflito se os dois estiverem de pé
    ao mesmo tempo).
    """
    return URL_BASE_E2E


@pytest.fixture
def login_admin():
    """
    Cria um profissional administrador via API (nesse banco E2E isolado,
    não pressupõe que ele já exista) e retorna suas credenciais + token.
    """
    email = f"admin.e2e.{uuid.uuid4().hex[:8]}@exemplo.com"
    senha = "senha123"
    nome = "Admin E2E"

    resposta_criacao = requests.post(
        f"{URL_BASE_E2E}/profissionais/",
        json={
            "nome": nome,
            "email": email,
            "senha": senha,
            "nivel_acesso": "administrador",
        },
        timeout=5,
    )
    resposta_criacao.raise_for_status()
    profissional = resposta_criacao.json()

    resposta_login = requests.post(
        f"{URL_BASE_E2E}/auth/login",
        json={"email": email, "senha": senha},
        timeout=5,
    )
    resposta_login.raise_for_status()
    dados_login = resposta_login.json()

    return {
        "nome": nome,
        "email": email,
        "senha": senha,
        "profissional_id": profissional["id"],
        "token": dados_login["access_token"],
    }


@pytest.fixture
def pagina_logada_admin(page, login_admin):
    """
    Faz login como administrador através da própria UI (tela de login),
    deixando `page` com sessão ativa (token no localStorage) - reutilizável
    por qualquer teste de fluxo que precise começar já logado.
    """
    # wait_until="domcontentloaded" (em vez do padrão "load"): neste
    # ambiente, o evento "load" às vezes nunca dispara (algum sub-recurso
    # parece nunca "terminar" do ponto de vista do Chromium), enquanto o
    # DOM em si já está pronto e funcional bem antes disso. Confirmado
    # via depuração: chamadas HTTP puras (sem navegador) para essas
    # mesmas páginas sempre respondem rápido - o travamento é específico
    # do `goto`/`reload` esperando por "load".
    page.goto("/login.html", wait_until="domcontentloaded")
    page.fill("#email", login_admin["email"])
    page.fill("#senha", login_admin["senha"])
    page.click("button[type=submit]")
    page.wait_for_url(re.compile(r".*/index\.html$"))
    return page


def gerar_cpf_unico():
    """CPF (fictício) único o bastante para não colidir com outros testes na mesma sessão E2E."""
    return str(uuid.uuid4().int)[:11]


CONDICAO_TESTE_ENCAMINHAMENTO_EXAME = "Condição de teste E2E"


def cadastrar_paciente_via_ui(page, nome, data_nascimento, sexo):
    """
    Cadastra um paciente novo pela tela pacientes-cadastrar.html e
    espera o redirecionamento (automático, pós-sucesso) de volta para
    pacientes.html. Retorna o documento gerado (usado para localizar o
    paciente depois, via busca).

    NOTA: depois da navegação inicial, toda a navegação é feita por
    CLIQUES em links (nunca goto()/reload()) - neste ambiente, chamadas
    explícitas de Page.goto/Page.reload em sequência mostraram-se
    instáveis (ficam penduradas, mesmo com wait_until="domcontentloaded"),
    enquanto navegação por clique/redirecionamento via JS nunca falhou.
    """
    page.goto("/pacientes-cadastrar.html", wait_until="domcontentloaded")
    documento = gerar_cpf_unico()
    page.fill("#nome", nome)
    page.fill("#dataNascimento", data_nascimento)
    page.select_option("#sexo", sexo)
    page.fill("#documento", documento)
    page.click("#formPaciente button[type=submit]")
    page.wait_for_url(re.compile(r".*/pacientes\.html$"))
    return documento


def criar_consulta_de_teste_encaminhamento_exame(page):
    """
    Cadastra um paciente e uma consulta novos via UI e deixa `page`
    posicionada em consultas.html, com a nova consulta visível na
    tabela. Retorna o documento do paciente (usado para reencontrar a
    linha depois). Compartilhado por test_fluxo_encaminhamento.py e
    test_fluxo_exame.py (arquivos separados de propósito - ver
    "Problema conhecido" no README.md).
    """
    documento = cadastrar_paciente_via_ui(page, "Paciente E2E Encaminhamento/Exame", "1978-11-02", "M")

    page.fill("#buscaPaciente", documento)
    linha_paciente = page.locator("#corpoTabelaPacientes tr", has_text=documento)
    linha_paciente.wait_for()
    linha_paciente.get_by_role("link", name="Ver consultas").click()
    page.wait_for_url(re.compile(r".*/consultas\.html\?paciente_id=\d+$"))

    page.fill("#condicao", CONDICAO_TESTE_ENCAMINHAMENTO_EXAME)
    page.click("#formConsulta button[type=submit]")
    page.wait_for_url(re.compile(r".*/anamnese\.html\?consulta_id=\d+$"))

    voltar_para_consultas_do_paciente(page, documento)
    return documento


def voltar_para_consultas_do_paciente(page, documento):
    """Navega (via cliques) de volta para a tela de consultas do paciente de teste, usando a busca."""
    page.get_by_role("link", name="Pacientes").click()
    page.wait_for_url(re.compile(r".*/pacientes\.html$"))

    page.fill("#buscaPaciente", documento)
    linha_paciente = page.locator("#corpoTabelaPacientes tr", has_text=documento)
    linha_paciente.wait_for()
    linha_paciente.get_by_role("link", name="Ver consultas").click()
    page.wait_for_url(re.compile(r".*/consultas\.html\?paciente_id=\d+$"))


def montar_heredograma_fake(consulta_id):
    """
    Heredograma fake, no MESMO formato que a API real retornaria -
    usado para mockar tanto POST .../gerar-heredograma quanto GET
    .../heredograma, evitando qualquer chamada real à API da Anthropic.
    """
    return {
        "consulta_id": int(consulta_id),
        "individuos": [
            {
                "id": 1,
                "consulta_id": int(consulta_id),
                "codigo": "I.1",
                "geracao": 1,
                "posicao": 1,
                "papel_descricao": "Pai",
                "observacao": None,
                "sexo": "M",
                "afetado": True,
                "portador": False,
                "falecido": False,
                "probando": False,
                "cid_sugerido": "C61",
            },
            {
                "id": 2,
                "consulta_id": int(consulta_id),
                "codigo": "II.1",
                "geracao": 2,
                "posicao": 1,
                "papel_descricao": "Paciente",
                "observacao": None,
                "sexo": "F",
                "afetado": False,
                "portador": False,
                "falecido": False,
                "probando": True,
                "cid_sugerido": None,
            },
        ],
        "relacionamentos": [
            {
                "id": 1,
                "consulta_id": int(consulta_id),
                "tipo": "filiacao",
                "origem_codigo": "I.1",
                "destino_codigo": "II.1",
                "consanguineo": False,
            },
        ],
    }


def gerar_heredograma_de_teste(page):
    """
    Cadastra paciente+consulta via UI, responde 3 perguntas do roteiro,
    mocka a geração de heredograma (evita chamada real à API da
    Anthropic - ver montar_heredograma_fake) e navega até a tela de
    heredograma, esperando o SVG e os botões de exportação ficarem
    prontos. Retorna o consulta_id. Compartilhado por
    test_fluxo_consulta_heredograma.py e test_exportar_heredograma.py.
    """
    from playwright.sync_api import expect

    documento = cadastrar_paciente_via_ui(page, "Paciente E2E Heredograma", "1985-03-20", "F")

    page.fill("#buscaPaciente", documento)
    linha_paciente = page.locator("#corpoTabelaPacientes tr", has_text=documento)
    linha_paciente.wait_for()
    linha_paciente.get_by_role("link", name="Ver consultas").click()
    page.wait_for_url(re.compile(r".*/consultas\.html\?paciente_id=\d+$"))

    page.fill("#condicao", "Predisposição hereditária a câncer de mama e ovário")
    page.click("#formConsulta button[type=submit]")
    page.wait_for_url(re.compile(r".*/anamnese\.html\?consulta_id=\d+$"))
    consulta_id = re.search(r"consulta_id=(\d+)", page.url).group(1)

    for _ in range(3):
        textarea = page.locator("[id^='resposta-']").first
        textarea.wait_for()
        pergunta_id = textarea.get_attribute("id").split("-", 1)[1]

        textarea.fill(f"Resposta de teste E2E para a pergunta {pergunta_id}.")
        botao_salvar = page.locator(f'[data-acao="salvar-nova"][data-pergunta-id="{pergunta_id}"]')
        botao_salvar.click()
        # Ver nota em test_fluxo_consulta_heredograma.py (histórico) sobre
        # por que esperamos o botão sumir do DOM, e não uma resposta de rede.
        botao_salvar.wait_for(state="detached")

    heredograma_fake = montar_heredograma_fake(consulta_id)

    def _responder_com_heredograma_fake(route):
        route.fulfill(status=200, content_type="application/json", body=json.dumps(heredograma_fake))

    page.route(f"**/consultas/{consulta_id}/gerar-heredograma", _responder_com_heredograma_fake)
    page.route(f"**/consultas/{consulta_id}/heredograma", _responder_com_heredograma_fake)

    page.click("#btnGerarHeredograma")
    mensagem = page.locator("#mensagemGeracao")
    mensagem.wait_for()

    link_heredograma = page.locator("#linkHeredograma a", has_text="Ver heredograma")
    link_heredograma.wait_for()
    link_heredograma.click()
    page.wait_for_url(re.compile(r".*/heredograma\.html\?consulta_id=\d+$"))

    svg = page.locator("#heredogramaContainer svg")
    svg.wait_for()

    # Os botões de exportação só habilitam depois que script.js busca os
    # dados complementares da consulta/paciente (ver prepararExportacao em
    # exportar-heredograma.js) - espera isso terminar antes de devolver.
    expect(page.locator("#btnExportarPdf")).to_be_enabled()

    return consulta_id
