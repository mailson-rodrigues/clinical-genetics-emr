import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.database import Base, engine
from app.rate_limit import limiter
from app.models.paciente import Paciente
from app.models.anamnese import Pergunta, Consulta, Resposta
from app.models.heredograma import Individuo, Relacionamento
from app.models.historico_clinico import (
    Alergia, Doenca, Cirurgia, HistoricoClinico, Operadora, PacienteConvenio
)
from app.models.cid import Cid
from app.models.profissional import Especialidade, Profissional
from app.models.log_auditoria import LogAuditoria
from app.models.encaminhamento import Encaminhamento
from app.models.exame import Exame
from app.models.perfil_acesso import Modulo, PerfilAcesso, PerfilAcessoModulo
from app.models.anexo import Anexo
from app.models.hipotese import HipoteseDiagnostica, FonteHipotese
from app.routes import (
    paciente, pergunta, consulta, historico_clinico, cid, profissional, auth,
    log_auditoria, encaminhamento, exame, perfil_acesso, dashboard, anexo, hipotese
)
from app.middlewares import middleware_log_auditoria

app = FastAPI(title="Heredograma IA")

# Rate limiting (slowapi) - protege rotas sensíveis (ex: a que chama a API
# paga da Anthropic) contra abuso. O limite em si é declarado por rota via
# @limiter.limit(...) (ver app/routes/consulta.py); aqui só registramos a
# instância compartilhada e o handler que converte estouro de limite em
# HTTP 429.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Em desenvolvimento local, sem nenhuma configuração extra, libera qualquer
# origem ("*"). Em produção, defina ALLOWED_ORIGINS no .env com o(s)
# domínio(s) real(is) do frontend, separados por vírgula, ex:
#   ALLOWED_ORIGINS=https://app.exemplo.com,https://exemplo.com
origens_permitidas_env = os.getenv("ALLOWED_ORIGINS")
origens_permitidas = (
    [origem.strip() for origem in origens_permitidas_env.split(",")]
    if origens_permitidas_env
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origens_permitidas,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(BaseHTTPMiddleware, dispatch=middleware_log_auditoria)

app.include_router(auth.router)
app.include_router(paciente.router)
app.include_router(pergunta.router)
app.include_router(consulta.router)
app.include_router(historico_clinico.router)
app.include_router(historico_clinico.router_operadoras)
app.include_router(cid.router)
app.include_router(profissional.router)
app.include_router(profissional.router_especialidades)
app.include_router(log_auditoria.router)
app.include_router(encaminhamento.router)
app.include_router(exame.router)
app.include_router(perfil_acesso.router_modulos)
app.include_router(perfil_acesso.router)
app.include_router(dashboard.router)
app.include_router(anexo.router_pacientes)
app.include_router(anexo.router_exames)
app.include_router(anexo.router_anexos)
app.include_router(hipotese.router)


@app.get("/api/status")
def status():
    return {"status": "API rodando com sucesso"}


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")