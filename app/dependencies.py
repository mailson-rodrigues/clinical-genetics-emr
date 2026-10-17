from typing import Optional

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError

from app.database import get_db
from app.models.perfil_acesso import Modulo, PerfilAcessoModulo
from app.models.profissional import Profissional
from app.services.seguranca import decodificar_token

# HTTPBearer is recognized by Swagger as a real "security scheme",
# which makes the global "Authorize" button (padlock) appear at the
# top of the /docs page, working for all protected routes at
# once - unlike the manual Header we used before.
esquema_bearer = HTTPBearer()

# auto_error=False: does not raise 401 when there is no Authorization header -
# used on public routes that only need to know WHO the professional is
# (if any) to decide something conditionally (e.g. unlock an
# extra parameter only for administrators), without requiring everyone to log in.
esquema_bearer_opcional = HTTPBearer(auto_error=False)


def obter_profissional_atual(
    credenciais: HTTPAuthorizationCredentials = Depends(esquema_bearer),
    db: Session = Depends(get_db),
) -> Profissional:
    """
    Extracts and validates the JWT token (via the Bearer scheme), returning the
    matching Profissional. Used to protect routes that require login.
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
    Like `obter_profissional_atual`, but returns None instead of raising 401
    when there is no token - for public routes that need to identify the
    professional only when they are logged in. A token that is PRESENT but
    invalid/expired still raises 401 (avoids masking a corrupted token).
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
    Additional dependency: requires the logged-in professional to have
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
    Dependency factory (a dependency with a parameter): returns a
    dependency that requires login AND access to the given module via
    Access Profile - unless the professional is an administrator,
    who always has full access regardless of profile.

    Usage: `Depends(exigir_acesso_modulo("consultas"))` in place of
    `Depends(obter_profissional_atual)` on routes that must respect
    the granular access profile.
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