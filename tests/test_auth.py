from app.models.profissional import Profissional
from app.services.seguranca import gerar_hash_senha


def _criar_profissional(db_session, email="dra.teste@exemplo.com", senha="senha123"):
    profissional = Profissional(
        nome="Dra. Teste",
        email=email,
        senha_hash=gerar_hash_senha(senha),
        nivel_acesso="profissional",
    )
    db_session.add(profissional)
    db_session.commit()
    db_session.refresh(profissional)
    return profissional


def test_login_com_credenciais_corretas(client, db_session):
    _criar_profissional(db_session, email="dra.teste@exemplo.com", senha="senha123")

    resposta = client.post("/auth/login", json={"email": "dra.teste@exemplo.com", "senha": "senha123"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["access_token"]
    assert corpo["token_type"] == "bearer"
    assert corpo["nivel_acesso"] == "profissional"


def test_login_com_senha_errada(client, db_session):
    _criar_profissional(db_session, email="dra.teste@exemplo.com", senha="senha123")

    resposta = client.post("/auth/login", json={"email": "dra.teste@exemplo.com", "senha": "senha-errada"})

    assert resposta.status_code == 401


def test_login_com_email_inexistente(client, db_session):
    resposta = client.post("/auth/login", json={"email": "nao.existe@exemplo.com", "senha": "qualquer"})

    assert resposta.status_code == 401


def test_login_bloqueia_apos_10_tentativas_por_minuto(client, db_session):
    """
    Rate limiting (10/minute por IP, ver @limiter.limit em
    app/routes/auth.py) contra força bruta de senha. O resultado de cada
    tentativa individual não importa (aqui todas erram a senha de
    propósito) - o que importa é que a 11ª tentativa dentro da mesma
    janela de 1 minuto seja barrada com 429 antes mesmo de chegar à
    verificação de senha.
    """
    _criar_profissional(db_session, email="dra.teste@exemplo.com", senha="senha123")

    for _ in range(10):
        resposta = client.post(
            "/auth/login", json={"email": "dra.teste@exemplo.com", "senha": "senha-errada"}
        )
        assert resposta.status_code == 401

    decima_primeira = client.post(
        "/auth/login", json={"email": "dra.teste@exemplo.com", "senha": "senha-errada"}
    )
    assert decima_primeira.status_code == 429


def test_auth_me_retorna_dados_do_profissional_logado(client, profissional_info):
    resposta = client.get("/auth/me", headers={"Authorization": f"Bearer {profissional_info['token']}"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["id"] == profissional_info["profissional_id"]
    assert corpo["nivel_acesso"] == "profissional"


def test_auth_me_sem_login(client):
    resposta = client.get("/auth/me")

    assert resposta.status_code == 401


def test_redefinir_senha_como_admin(client, db_session, admin_token):
    _criar_profissional(db_session, email="esqueceu@exemplo.com", senha="senha-antiga")

    resposta = client.post(
        "/auth/redefinir-senha",
        json={"email": "esqueceu@exemplo.com", "nova_senha": "senha-nova"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resposta.status_code == 200

    login_com_senha_antiga = client.post(
        "/auth/login", json={"email": "esqueceu@exemplo.com", "senha": "senha-antiga"}
    )
    assert login_com_senha_antiga.status_code == 401

    login_com_senha_nova = client.post(
        "/auth/login", json={"email": "esqueceu@exemplo.com", "senha": "senha-nova"}
    )
    assert login_com_senha_nova.status_code == 200


def test_redefinir_senha_sem_ser_admin(client, db_session, profissional_token):
    _criar_profissional(db_session, email="esqueceu2@exemplo.com", senha="senha-antiga")

    resposta = client.post(
        "/auth/redefinir-senha",
        json={"email": "esqueceu2@exemplo.com", "nova_senha": "senha-nova"},
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 403


def test_redefinir_senha_email_inexistente(client, admin_token):
    resposta = client.post(
        "/auth/redefinir-senha",
        json={"email": "nao.existe@exemplo.com", "nova_senha": "senha-nova"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert resposta.status_code == 404
