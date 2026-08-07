# Heredograma IA

Sistema de apoio ao aconselhamento genético: conduz a anamnese de um
paciente e usa IA (Claude) para gerar automaticamente o heredograma
(pedigree) da família investigada. Backend em FastAPI + SQLAlchemy +
Alembic; frontend em HTML/JS/CSS puro, servido como estático.

## Módulos funcionais

- **Pacientes**: cadastro completo (dados pessoais, endereço, LGPD,
  responsável), edição e remoção (soft delete), restritas a
  administradores.
- **Anamnese**: roteiro de perguntas por categoria, respostas
  editáveis, vinculadas a uma consulta.
- **Heredograma via IA**: gera (ou regera) o heredograma a partir das
  respostas da anamnese, usando a API da Anthropic (Claude); limitado
  por rate limiting (60/minuto por IP).
- **Histórico clínico**: alergias, doenças (com vínculo opcional a um
  código CID), cirurgias e históricos gerais por paciente.
- **CID**: catálogo de códigos CID-10 (código, descrição, capítulo),
  com busca; gerenciado pela tela de Catálogos.
- **Convênios/Operadoras**: catálogo de operadoras de saúde e vínculo
  paciente-convênio; gerenciado pela tela de Catálogos.
- **Profissionais**: cadastro de profissionais e especialidades,
  níveis de acesso (profissional/administrador).
- **Perfis de acesso**: perfis configuráveis, vinculando módulos do
  sistema a cada perfil, atribuídos a profissionais.
- **Logs de auditoria**: registro automático de requisições
  sensíveis, com tela de consulta filtrável (restrita a
  administradores).
- **Encaminhamentos**: encaminhamento de paciente a uma especialidade,
  vinculado a uma consulta, com fluxo de status.
- **Exames**: registro de exames e resultados, vinculados a uma
  consulta.
- **Exportação de heredograma**: exportação do heredograma exibido em
  PDF (vetorial) e PNG (raster), gerada inteiramente no navegador.
- **Catálogos administrativos**: tela única para cadastrar e listar
  códigos CID e operadoras (restrita a administradores).

## Configuração local

1. Instale as dependências: `pip install -r requirements.txt`
2. Copie `.env.example` para `.env` e preencha `ANTHROPIC_API_KEY` e `JWT_SECRET_KEY`.
3. Rode as migrações: `alembic upgrade head`
4. Suba o servidor: `uvicorn app.main:app --reload`

## Como rodar os testes

O comando oficial para rodar **toda** a suíte de testes do projeto
(backend + end-to-end) é:

```
python executar_todos_os_testes.py
```

Esse único comando roda os testes de backend (`pytest tests/`) e os
testes end-to-end (`run_e2e_tests.py`) em sequência e imprime um resumo
geral claro ao final, no formato:

```
==================================================
RESUMO GERAL DOS TESTES
==================================================
Backend (pytest):        OK - X passed
End-to-end (Playwright): OK - Y arquivo(s) passaram
==================================================
RESULTADO FINAL: TUDO PASSOU
==================================================
```

(`X` e `Y` variam conforme o projeto cresce - não são fixados aqui de
propósito, para o exemplo não ficar desatualizado a cada teste novo.)

Se algum grupo falhar, o resumo indica exatamente qual (backend e/ou
end-to-end) e quantos testes, e a saída completa daquele grupo é
exibida acima do resumo para diagnóstico. O código de saída é `0` se
tudo passou e `1` caso contrário - pronto para uso em CI.

### Rodando só uma parte (desenvolvimento)

Os comandos individuais continuam existindo para quem quiser rodar só
uma parte da suíte durante o desenvolvimento, mas **não são** o fluxo
recomendado do dia a dia:

```
pytest tests/ -v              # só os testes de backend
python run_e2e_tests.py       # só os testes end-to-end (todos os arquivos)
pytest tests_e2e/test_X.py -v # só um arquivo e2e específico
```

Mais detalhes sobre os testes end-to-end (Playwright), incluindo o
modo headless/headed e um problema conhecido de instabilidade ao rodar
`pytest tests_e2e/ -v` diretamente, estão em [tests_e2e/README.md](tests_e2e/README.md).
