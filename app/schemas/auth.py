from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    profissional_id: int
    nome: str
    nivel_acesso: str


class RedefinirSenhaRequest(BaseModel):
    email: EmailStr
    nova_senha: str