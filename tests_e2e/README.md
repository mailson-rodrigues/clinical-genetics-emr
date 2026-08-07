# Testes E2E (ponta a ponta)

Testes de navegador (Playwright) que exercitam o sistema completo:
frontend real + servidor real (FastAPI/uvicorn) + banco real (SQLite),
tudo automatizado por `tests_e2e/conftest.py` - não é necessário abrir
nenhum terminal adicional, subir servidor manualmente, ou ter um banco
pré-existente.

## Como rodar

O comando oficial para rodar a suíte completa, de forma 100%
automatizada e com um único comando, é:

```
python run_e2e_tests.py
```

Ele roda cada arquivo `test_*.py` de `tests_e2e/` como um subprocesso
`pytest` **separado** e imprime um resumo no final (quantos arquivos
passaram/falharam), com código de saída != 0 se algum falhar - pronto
para pipelines de CI. Ver a seção "Problema conhecido" abaixo para o
motivo de existir esse script em vez de rodar `pytest tests_e2e/ -v`
diretamente.

### Por baixo dos panos

Cada arquivo, ao rodar (seja via `run_e2e_tests.py` ou diretamente via
`pytest tests_e2e/test_X.py -v`):

1. Cria um banco SQLite temporário e isolado (`test_e2e.db`, na raiz do
   projeto) - nunca o `heredograma.db` real, nem o banco usado pelos
   testes de backend em `tests/`.
2. Roda `alembic upgrade head` nesse banco.
3. Roda `seed_perguntas.py` nesse banco (popula o roteiro de anamnese -
   necessário para os testes que respondem perguntas pela UI).
4. Sobe a aplicação real (`uvicorn app.main:app`) na porta **8001**
   (diferente da 8000 do servidor de desenvolvimento, para não haver
   conflito caso os dois estejam de pé ao mesmo tempo).
5. Espera o servidor responder em `/api/status` antes de rodar os testes.
6. Ao final, encerra o servidor e apaga o `test_e2e.db`.

Tudo isso acontece dentro do fixture `servidor_e2e` (sessão, autouse) em
`conftest.py` - você não precisa fazer nada disso manualmente.

## Modo headless (padrão) vs. inspeção visual

Por padrão (e sem nenhuma flag extra), os testes rodam com o navegador
**headless** (sem interface visível) - é o padrão do pytest-playwright e
o que deve ser usado em execução automática/CI.

Se você quiser **ver o navegador rodando** (útil para depurar um teste
com falha, ou só para acompanhar visualmente), rode o arquivo
específico com:

```
pytest tests_e2e/test_X.py -v --headed --slowmo 500
```

Isso é **opcional** e não faz parte da execução automática padrão.

## Problema conhecido: rodar `pytest tests_e2e/ -v` diretamente

Cada arquivo de teste, rodado sozinho, passa de forma confiável. Rodar
TODOS os arquivos juntos numa única sessão do pytest
(`pytest tests_e2e/ -v`) hoje é instável: a partir do segundo fluxo
completo de navegador da sessão (login+cadastro+consulta), algum teste
trava numa navegação, e a partir daí o próprio servidor (uvicorn) para
de responder a outros clientes também. Foi isolado extensivamente -
não é causado por concorrência/lentidão do SQLite, CPU throttling do
ambiente, estratégia de navegação (goto vs. clique), reuso de
contexto/página do Playwright, nem timeout de keep-alive do uvicorn
(todas essas hipóteses foram testadas e descartadas em sessão de
depuração anterior). Ambiente de teste apenas - não deve se reproduzir
em produção.

Por isso existe o `run_e2e_tests.py`: rodando cada arquivo em seu
próprio processo `pytest` (portanto, seu próprio servidor E2E do zero),
o problema é evitado por completo. Use sempre `python run_e2e_tests.py`
como comando oficial; `pytest tests_e2e/ -v` direto continua disponível
para rodar um arquivo específico (`pytest tests_e2e/test_X.py -v`), mas
não deve ser usado para rodar o diretório inteiro de uma vez.

## Escrevendo novos testes

- Use o fixture `page` (do pytest-playwright) normalmente - navegações
  relativas (`page.goto("/pacientes.html")`) já resolvem contra o
  `base_url` do servidor E2E automaticamente.
- Use o fixture `login_admin` para obter um profissional administrador
  já criado (via API) nesse banco de teste, com `email`/`senha`/`token`
  prontos - não pressuponha que ele já existe.
