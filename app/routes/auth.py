from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.profissional import Profissional
from app.rate_limit import limiter
from app.schemas.auth import LoginRequest, TokenResponse, RedefinirSenhaRequest
from app.schemas.profissional import ProfissionalResponse
from app.services.seguranca import verificar_senha, criar_token_acesso, gerar_hash_senha
from app.dependencies import obter_profissional_atual, exigir_administrador

router = APIRouter(prefix="/auth", tags=["Autenticacao"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, dados: LoginRequest, db: Session = Depends(get_db)):
    """
    Autentica um profissional por e-mail e senha, retornando um token de
    acesso.

    Limitada a 10 tentativas/minuto por IP (@limiter.limit) para dificultar
    força bruta de senha. Excedido o limite, responde 429 Too Many Requests.
    """
    profissional = db.query(Profissional).filter(Profissional.email == dados.email).first()

    if not profissional or not verificar_senha(dados.senha, profissional.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")

    if not profissional.ativo:
        raise HTTPException(status_code=401, detail="Este profissional está inativo.")

    token = criar_token_acesso({"profissional_id": profissional.id})

    return TokenResponse(
        access_token=token,
        profissional_id=profissional.id,
        nome=profissional.nome,
        nivel_acesso=profissional.nivel_acesso,
    )


@router.get("/me", response_model=ProfissionalResponse)
def obter_sessao_atual(profissional_atual: Profissional = Depends(obter_profissional_atual)):
    """Retorna os dados do profissional dono do token atual - útil para o frontend confirmar a sessão."""
    return profissional_atual


@router.post("/redefinir-senha", response_model=ProfissionalResponse)
def redefinir_senha(
    dados: RedefinirSenhaRequest,
    db: Session = Depends(get_db),
    _administrador: Profissional = Depends(exigir_administrador),
):
    """
    Redefine a senha de um profissional a partir do e-mail. Requer login
    como ADMINISTRADOR.

    LIMITAÇÃO CONHECIDA: esta é uma redefinição ADMINISTRATIVA - não há
    fluxo de autoatendimento (link por e-mail, código de verificação,
    etc.). O profissional que esqueceu a senha precisa pedir para um
    administrador redefini-la por aqui.
    """
    profissional = db.query(Profissional).filter(Profissional.email == dados.email).first()
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado.")

    profissional.senha_hash = gerar_hash_senha(dados.nova_senha)
    db.commit()
    db.refresh(profissional)
    return profissional