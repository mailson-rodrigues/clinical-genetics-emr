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

# Isolated SQLite database, exclusive to the E2E tests - never the real
# (dev) heredograma.db nor the test_heredograma.db used by the backend tests in
# tests/ (which run in-process, without starting a real server).
DATABASE_URL_E2E = f"sqlite:///{CAMINHO_BANCO_E2E.as_posix()}"

PORTA_SERVIDOR_E2E = 8001
URL_BASE_E2E = f"http://127.0.0.1:{PORTA_SERVIDOR_E2E}"


def _remover_banco_e2e():
    """
    On Windows, the OS may take a moment to release the handle of the
    SQLite file after the uvicorn process is terminated - retries
    a few times before giving up, instead of failing the teardown.
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
    """Polls /api/status until the server answers, or fails with a clear error."""
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
    Starts the real application (uvicorn) in a separate process, on a temporary,
    isolated SQLite database, so the E2E tests (Playwright)
    exercise the system end to end with a single command - without
    needing any manual terminal, an already-running server, or a
    pre-existing database.
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

    # The migrations only create the schema (empty tables) - the anamnesis
    # script is populated separately (same process used in production, see
    # seed_perguntas.py), needed so the anamnesis/pedigree
    # flow tests have real questions to answer in the UI.
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
            # The uvicorn default is to close idle keep-alive connections after
            # only 5s. UI tests have real pauses between actions (filling in
            # fields, waiting for elements) that may exceed that - when the
            # browser tries to reuse a connection that the server
            # has just closed for inactivity, the request hangs
            # until the Playwright timeout (it was exactly this
            # o sintoma: page.goto/reload/wait_for_url travando sempre a
            # from the 2nd test of the session onward, never reproducible via pure HTTP
            # calls - only via a real browser, with real pauses).
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
    Overrides the pytest-playwright `base_url` fixture: instead of
    depending on the --base-url command-line flag, it always points to
    the local E2E server (port 8001, different from 8000 of the development
    server, so there is no conflict if both are up
    at the same time).
    """
    return URL_BASE_E2E


@pytest.fixture
def login_admin():
    """
    Creates an administrator professional via API (in this isolated E2E database,
    does not assume it already exists) and returns their credentials + token.
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
    Logs in as administrator through the UI itself (login screen),
    leaving `page` with an active session (token in localStorage) - reusable
    by any flow test that needs to start already logged in.
    """
    # wait_until="domcontentloaded" (instead of the default "load"): in this
    # ambiente, o evento "load" às vezes nunca dispara (algum sub-recurso
    # seems to never "finish" from Chromium's point of view), while the
    # DOM itself is ready and functional well before that. Confirmed
    # via debugging: pure HTTP calls (without a browser) to those
    # same pages always answer quickly - the hang is specific
    # to `goto`/`reload` waiting for "load".
    page.goto("/login.html", wait_until="domcontentloaded")
    page.fill("#email", login_admin["email"])
    page.fill("#senha", login_admin["senha"])
    page.click("button[type=submit]")
    page.wait_for_url(re.compile(r".*/index\.html$"))
    return page


def gerar_cpf_unico():
    """A (fictitious) CPF unique enough not to collide with other tests in the same E2E session."""
    return str(uuid.uuid4().int)[:11]


CONDICAO_TESTE_ENCAMINHAMENTO_EXAME = "Condição de teste E2E"


def cadastrar_paciente_via_ui(page, nome, data_nascimento, sexo):
    """
    Registers a new patient through the pacientes-cadastrar.html screen and
    waits for the (automatic, post-success) redirect back to
    pacientes.html. Returns the generated document (used to locate the
    patient later, via search).

    NOTE: after the initial navigation, all navigation is done by
    CLICKS on links (never goto()/reload()) - in this environment, explicit
    calls to Page.goto/Page.reload in sequence proved
    unstable (they hang, even with wait_until="domcontentloaded"),
    while navigation by click/redirect via JS never failed.
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
    Registers a new patient and a new consultation via the UI and leaves `page`
    positioned on consultas.html, with the new consultation visible in the
    table. Returns the patient document (used to find the
    row again later). Shared by test_fluxo_encaminhamento.py and
    test_fluxo_exame.py (separate files on purpose - see
    "Known issue" in README.md).
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
    """Navigates (via clicks) back to the test patient's consultations screen, using the search."""
    page.get_by_role("link", name="Pacientes").click()
    page.wait_for_url(re.compile(r".*/pacientes\.html$"))

    page.fill("#buscaPaciente", documento)
    linha_paciente = page.locator("#corpoTabelaPacientes tr", has_text=documento)
    linha_paciente.wait_for()
    linha_paciente.get_by_role("link", name="Ver consultas").click()
    page.wait_for_url(re.compile(r".*/consultas\.html\?paciente_id=\d+$"))


def montar_heredograma_fake(consulta_id):
    """
    Fake pedigree, in the SAME format the real API would return -
    used to mock both POST .../gerar-heredograma and GET
    .../heredograma, avoiding any real call to the Anthropic API.
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
    Registers a patient + consultation via the UI, answers 3 questions of the script,
    mocks the pedigree generation (avoids a real call to the
    Anthropic API - see montar_heredograma_fake) and navigates to the
    pedigree screen, waiting for the SVG and the export buttons to become
    ready. Returns the consulta_id. Shared by
    test_fluxo_consulta_heredograma.py and test_exportar_heredograma.py.
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
        # See the note in test_fluxo_consulta_heredograma.py (history) about
        # why we wait for the button to disappear from the DOM, and not for a network response.
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

    # The export buttons are only enabled after script.js fetches the
    # complementary data of the consultation/patient (see prepararExportacao in
    # exportar-heredograma.js) - waits for that to finish before returning.
    expect(page.locator("#btnExportarPdf")).to_be_enabled()

    return consulta_id
