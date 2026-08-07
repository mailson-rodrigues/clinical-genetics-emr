from app.models.anexo import Anexo
from app.services import armazenamento

CONTEUDO_PDF_FAKE = b"%PDF-1.4 conteudo fake de teste"


def _upload_paciente(client, paciente_id, token, nome="laudo.pdf", conteudo=CONTEUDO_PDF_FAKE, tipo="application/pdf"):
    return client.post(
        f"/pacientes/{paciente_id}/anexos",
        files={"arquivo": (nome, conteudo, tipo)},
        headers={"Authorization": f"Bearer {token}"},
    )


def _upload_exame(client, exame_id, token, nome="resultado.pdf", conteudo=CONTEUDO_PDF_FAKE, tipo="application/pdf"):
    return client.post(
        f"/exames/{exame_id}/anexos",
        files={"arquivo": (nome, conteudo, tipo)},
        headers={"Authorization": f"Bearer {token}"},
    )


def _criar_exame(client, consulta_id, token):
    resposta = client.post(
        f"/consultas/{consulta_id}/exames",
        json={"tipo_exame": "Painel BRCA1/BRCA2"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_upload_anexo_paciente(client, paciente_exemplo, profissional_token):
    resposta = _upload_paciente(client, paciente_exemplo["id"], profissional_token)

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["paciente_id"] == paciente_exemplo["id"]
    assert corpo["exame_id"] is None
    assert corpo["nome_original"] == "laudo.pdf"
    assert corpo["tipo_conteudo"] == "application/pdf"
    assert corpo["tamanho_bytes"] == len(CONTEUDO_PDF_FAKE)


def test_upload_anexo_exame(client, consulta_exemplo, profissional_token):
    exame = _criar_exame(client, consulta_exemplo["id"], profissional_token)

    resposta = _upload_exame(client, exame["id"], profissional_token)

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["exame_id"] == exame["id"]
    assert corpo["paciente_id"] is None


def test_upload_tipo_invalido_e_rejeitado(client, paciente_exemplo, profissional_token):
    resposta = _upload_paciente(
        client, paciente_exemplo["id"], profissional_token,
        nome="virus.exe", conteudo=b"conteudo qualquer", tipo="application/x-msdownload",
    )

    assert resposta.status_code == 400
    assert "não permitido" in resposta.json()["detail"].lower()


def test_upload_arquivo_grande_demais_e_rejeitado(client, paciente_exemplo, profissional_token, db_session):
    conteudo_grande = b"x" * (armazenamento.TAMANHO_MAXIMO_BYTES + 1)

    resposta = _upload_paciente(client, paciente_exemplo["id"], profissional_token, conteudo=conteudo_grande)

    assert resposta.status_code == 400
    assert "grande" in resposta.json()["detail"].lower()
    # Nada deve ter sido gravado (nem registro, nem arquivo em disco)
    assert db_session.query(Anexo).count() == 0


def test_listar_anexos_paciente(client, paciente_exemplo, profissional_token):
    _upload_paciente(client, paciente_exemplo["id"], profissional_token, nome="doc1.pdf")
    _upload_paciente(client, paciente_exemplo["id"], profissional_token, nome="doc2.pdf")

    resposta = client.get(
        f"/pacientes/{paciente_exemplo['id']}/anexos",
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 200
    nomes = [item["nome_original"] for item in resposta.json()]
    assert sorted(nomes) == ["doc1.pdf", "doc2.pdf"]


def test_listar_anexos_exame(client, consulta_exemplo, profissional_token):
    exame = _criar_exame(client, consulta_exemplo["id"], profissional_token)
    _upload_exame(client, exame["id"], profissional_token)

    resposta = client.get(
        f"/exames/{exame['id']}/anexos",
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


def test_download_anexo_retorna_o_mesmo_conteudo_enviado(client, paciente_exemplo, profissional_token):
    anexo = _upload_paciente(client, paciente_exemplo["id"], profissional_token).json()

    resposta = client.get(
        f"/anexos/{anexo['id']}/download",
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 200
    assert resposta.content == CONTEUDO_PDF_FAKE
    assert resposta.headers["content-type"] == "application/pdf"


def test_download_anexo_requer_login(client, paciente_exemplo, profissional_token):
    anexo = _upload_paciente(client, paciente_exemplo["id"], profissional_token).json()

    resposta = client.get(f"/anexos/{anexo['id']}/download")

    assert resposta.status_code == 401


def test_remover_anexo_apaga_registro_e_arquivo_fisico(client, paciente_exemplo, profissional_token, db_session):
    anexo = _upload_paciente(client, paciente_exemplo["id"], profissional_token).json()

    anexo_no_banco = db_session.query(Anexo).filter(Anexo.id == anexo["id"]).first()
    caminho_arquivo = armazenamento.caminho_completo(anexo_no_banco.nome_armazenado)
    assert caminho_arquivo.exists()

    resposta = client.delete(
        f"/anexos/{anexo['id']}",
        headers={"Authorization": f"Bearer {profissional_token}"},
    )

    assert resposta.status_code == 204
    assert not caminho_arquivo.exists()
    assert db_session.query(Anexo).filter(Anexo.id == anexo["id"]).first() is None
