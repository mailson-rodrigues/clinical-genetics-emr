import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.middlewares as middlewares_module
import app.services.armazenamento as armazenamento_module
from app.database import Base, get_db
from app.main import app
from app.models.anamnese import Pergunta
from app.models.perfil_acesso import Modulo, PerfilAcesso, PerfilAcessoModulo
from app.models.profissional import Profissional
from app.rate_limit import limiter
from app.schemas.heredograma import HeredogramaExtraido
from app.services.seguranca import gerar_hash_senha

TEST_DATABASE_PATH = os.path.join(os.path.dirname(__file__), "..", "test_heredograma.db")
TEST_DATABASE_URL = f"sqlite:///{TEST_DATABASE_PATH}"

# Uploads de teste isolados do diretório uploads/ real (dev) - ver
# app/services/armazenamento.py (lido dinamicamente via
# armazenamento_module.DIRETORIO_UPLOADS, não importado por nome, para
# este monkeypatch funcionar).
TEST_UPLOAD_DIR = Path(os.path.dirname(__file__)) / ".." / "test_uploads"
armazenamento_module.DIRETORIO_UPLOADS = TEST_UPLOAD_DIR

engine_teste = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocalTeste = sessionmaker(autocommit=False, autoflush=False, bind=engine_teste)


def _get_db_teste():
    db = SessionLocalTeste()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _get_db_teste

# O middleware de auditoria abre sua própria sessão direto de
# app.database.SessionLocal (sem passar pelo Depends(get_db)), então
# precisa ser redirecionado também - senão os testes gravariam logs de
# auditoria no heredograma.db real mesmo com o get_db sobrescrito.
middlewares_module.SessionLocal = SessionLocalTeste


@pytest.fixture(autouse=True)
def tabelas_de_teste():
    Base.metadata.create_all(bind=engine_teste)
    yield
    Base.metadata.drop_all(bind=engine_teste)


@pytest.fixture(autouse=True)
def resetar_rate_limit():
    """
    O Limiter (slowapi) guarda os contadores em memória, na mesma
    instância global para todo o processo - sem isso, chamadas de um
    teste (ex: o que verifica o 429) contaminariam a contagem de outro
    teste que chama a mesma rota limitada (POST .../gerar-heredograma).
    """
    limiter.reset()
    yield


@pytest.fixture(scope="session", autouse=True)
def limpar_arquivo_de_teste():
    yield
    engine_teste.dispose()
    if os.path.exists(TEST_DATABASE_PATH):
        os.remove(TEST_DATABASE_PATH)
    shutil.rmtree(TEST_UPLOAD_DIR, ignore_errors=True)


@pytest.fixture
def client(tabelas_de_teste):
    return TestClient(app)


@pytest.fixture
def db_session(tabelas_de_teste):
    db = SessionLocalTeste()
    try:
        yield db
    finally:
        db.close()


MODULOS_CODIGOS = ["pacientes", "consultas", "historico_clinico", "encaminhamentos", "exames"]


def _obter_ou_criar_perfil_com_acesso_total(db_session):
    """
    Perfil de acesso com TODOS os módulos liberados - usado como padrão
    para os profissionais de teste "genéricos" (fixtures
    `profissional_token`/`profissional_info`), para não quebrar testes
    já existentes que dependiam de um profissional comum conseguir
    fazer de tudo antes da introdução dos Perfis de Acesso granulares.
    Testes que querem verificar RESTRIÇÃO de acesso criam seu próprio
    perfil limitado (ver tests/test_perfis_acesso.py).
    """
    perfil = db_session.query(PerfilAcesso).filter(PerfilAcesso.nome == "Perfil Total (testes)").first()
    if perfil:
        return perfil.id

    perfil = PerfilAcesso(nome="Perfil Total (testes)")
    db_session.add(perfil)
    db_session.flush()

    for codigo in MODULOS_CODIGOS:
        modulo = db_session.query(Modulo).filter(Modulo.codigo == codigo).first()
        if not modulo:
            modulo = Modulo(codigo=codigo, nome=codigo)
            db_session.add(modulo)
            db_session.flush()
        db_session.add(PerfilAcessoModulo(perfil_acesso_id=perfil.id, modulo_id=modulo.id))

    db_session.commit()
    return perfil.id


def _criar_profissional_e_logar(client, db_session, nivel_acesso, email):
    perfil_acesso_id = None
    if nivel_acesso == "profissional":
        perfil_acesso_id = _obter_ou_criar_perfil_com_acesso_total(db_session)

    profissional = Profissional(
        nome=f"Profissional Teste ({nivel_acesso})",
        email=email,
        senha_hash=gerar_hash_senha("senha123"),
        nivel_acesso=nivel_acesso,
        perfil_acesso_id=perfil_acesso_id,
    )
    db_session.add(profissional)
    db_session.commit()
    db_session.refresh(profissional)

    resposta = client.post("/auth/login", json={"email": email, "senha": "senha123"})
    assert resposta.status_code == 200, resposta.text
    return {
        "token": resposta.json()["access_token"],
        "profissional_id": profissional.id,
    }


@pytest.fixture
def admin_token(client, db_session):
    """Cria um profissional administrador, loga via API e retorna o token de acesso."""
    return _criar_profissional_e_logar(client, db_session, "administrador", "admin.teste@exemplo.com")["token"]


@pytest.fixture
def profissional_token(client, db_session):
    """Cria um profissional comum, loga via API e retorna o token de acesso."""
    return _criar_profissional_e_logar(client, db_session, "profissional", "profissional.teste@exemplo.com")["token"]


@pytest.fixture
def profissional_info(client, db_session):
    """Igual a `profissional_token`, mas também expõe o profissional_id (útil para conferir preenchimento automático)."""
    return _criar_profissional_e_logar(client, db_session, "profissional", "profissional.info@exemplo.com")


@pytest.fixture
def paciente_exemplo(client):
    """Cria um paciente de teste via API e retorna o corpo da resposta (dict)."""
    dados = {
        "nome": "Paciente Exemplo",
        "data_nascimento": "1990-01-01",
        "sexo": "F",
        "documento": "11111111111",
    }
    resposta = client.post("/pacientes/", json=dados)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


@pytest.fixture
def consulta_exemplo(client, paciente_exemplo, profissional_token):
    """Cria uma consulta de teste vinculada a `paciente_exemplo`, via API."""
    dados = {
        "paciente_id": paciente_exemplo["id"],
        "condicao_investigada": "Câncer de mama hereditário",
    }
    resposta = client.post(
        "/consultas/",
        json=dados,
        headers={"Authorization": f"Bearer {profissional_token}"},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


@pytest.fixture
def pergunta_exemplo(db_session):
    """
    Cria uma pergunta do roteiro de anamnese diretamente no banco (não há
    rota de criação - em produção isso é feito via seed_perguntas.py).
    """
    pergunta = Pergunta(
        codigo="CONDICAO_DESCRICAO",
        categoria="Condição investigada",
        texto="Descreva a característica ou doença que motivou a consulta.",
        ordem=1,
    )
    db_session.add(pergunta)
    db_session.commit()
    db_session.refresh(pergunta)
    return pergunta


@pytest.fixture
def heredograma_exemplo():
    """
    Retorno fixo e determinístico equivalente ao que a IA (Claude)
    retornaria para extrair_heredograma - usado para mockar a chamada
    real à API da Anthropic nos testes (ver app/services/ia_extracao.py).
    """
    return HeredogramaExtraido(
        individuos=[
            {
                "codigo": "I.1",
                "geracao": 1,
                "posicao": 1,
                "papel_descricao": "Avô paterno",
                "observacao": None,
                "sexo": "M",
                "afetado": False,
                "portador": False,
                "falecido": True,
                "probando": False,
                "cid_sugerido": None,
            },
            {
                "codigo": "II.1",
                "geracao": 2,
                "posicao": 1,
                "papel_descricao": "Pai",
                "observacao": "Câncer de próstata aos 65 anos",
                "sexo": "M",
                "afetado": True,
                "portador": False,
                "falecido": False,
                "probando": False,
                "cid_sugerido": "C61",
            },
            {
                "codigo": "III.1",
                "geracao": 3,
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
        relacionamentos=[
            {"tipo": "filiacao", "origem_codigo": "I.1", "destino_codigo": "II.1", "consanguineo": False},
            {"tipo": "filiacao", "origem_codigo": "II.1", "destino_codigo": "III.1", "consanguineo": False},
        ],
    )
