from typing import Optional

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError

from app.database import get_db
from app.models.perfil_acesso import Modulo, PerfilAcessoModulo
from app.models.profissional import Profissional
from app.services.seguranca import decodificar_token

# HTTPBearer é reconhecido pelo Swagger como um "esquema de segurança" de
# verdade, o que faz aparecer o botão global "Authorize" (cadeado) no
# topo da página /docs, funcionando para todas as rotas protegidas de
# uma vez - diferente do Header manual que usávamos antes.
esquema_bearer = HTTPBearer()

# auto_error=False: não lança 401 quando não há header Authorization -
# usado em rotas públicas que só precisam saber QUEM é o profissional
# (se houver) para decidir alguma coisa condicionalmente (ex: liberar um
# parâmetro extra só para administradores), sem exigir login de todo mundo.
esquema_bearer_opcional = HTTPBearer(auto_error=False)


def obter_profissional_atual(
    credenciais: HTTPAuthorizationCredentials = Depends(esquema_bearer),
    db: Session = Depends(get_db),
) -> Profissional:
    """
    Extrai e valida o token JWT (via esquema Bearer), retornando o
    Profissional correspondente. Usada para proteger rotas que exigem login.
    """
    token = credenciais.credentials

    try:
        payload = decodificar_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado. Faça login novamente.")

    profissional_id = payload.get("profissional_id")
    if profissional_id is None:
        raise HTTPException(status_code=401, detail="Token inválido.")

    profissional = db.query(Profissional).filter(Profissional.id == profissional_id).first()
    if not profissional or not profissional.ativo:
        raise HTTPException(status_code=401, detail="Profissional não encontrado ou inativo.")

    return profissional


def obter_profissional_opcional(
    credenciais: Optional[HTTPAuthorizationCredentials] = Depends(esquema_bearer_opcional),
    db: Session = Depends(get_db),
) -> Optional[Profissional]:
    """
    Como `obter_profissional_atual`, mas retorna None em vez de lançar 401
    quando não há token - para rotas públicas que precisam identificar o
    profissional apenas quando ele estiver logado. Um token PRESENTE mas
    inválido/expirado ainda lança 401 (evita mascarar um token corrompido).
    """
    if credenciais is None:
        return None

    try:
        payload = decodificar_token(credenciais.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado. Faça login novamente.")

    profissional_id = payload.get("profissional_id")
    if profissional_id is None:
        raise HTTPException(status_code=401, detail="Token inválido.")

    profissional = db.query(Profissional).filter(Profissional.id == profissional_id).first()
    if not profissional or not profissional.ativo:
        raise HTTPException(status_code=401, detail="Profissional não encontrado ou inativo.")

    return profissional


def exigir_administrador(
    profissional_atual: Profissional = Depends(obter_profissional_atual),
) -> Profissional:
    """
    Dependência adicional: exige que o profissional logado tenha
    nivel_acesso == 'administrador'.
    """
    if profissional_atual.nivel_acesso != "administrador":
        raise HTTPException(
            status_code=403,
            detail="Ação restrita a administradores.",
        )
    return profissional_atual


def exigir_acesso_modulo(codigo_modulo: str):
    """
    Fábrica de dependência (dependência com parâmetro): retorna uma
    dependência que exige login E acesso ao módulo informado via
    Perfil de Acesso - a menos que o profissional seja administrador,
    que sempre tem acesso total independente de perfil.

    Uso: `Depends(exigir_acesso_modulo("consultas"))` no lugar de
    `Depends(obter_profissional_atual)` nas rotas que devem respeitar
    o perfil de acesso granular.
    """
    def verificador(
        profissional_atual: Profissional = Depends(obter_profissional_atual),
        db: Session = Depends(get_db),
    ) -> Profissional:
        if profissional_atual.nivel_acesso == "administrador":
            return profissional_atual

        if not profissional_atual.perfil_acesso_id:
            raise HTTPException(status_code=403, detail="Seu perfil de acesso não permite esta ação.")

        tem_acesso = (
            db.query(PerfilAcessoModulo)
            .join(Modulo, Modulo.id == PerfilAcessoModulo.modulo_id)
            .filter(
                PerfilAcessoModulo.perfil_acesso_id == profissional_atual.perfil_acesso_id,
                Modulo.codigo == codigo_modulo,
            )
            .first()
        )
        if not tem_acesso:
            raise HTTPException(status_code=403, detail="Seu perfil de acesso não permite esta ação.")

        return profissional_atual

    return verificador