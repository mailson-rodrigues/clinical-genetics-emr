# E2E (end-to-end) tests

Browser tests (Playwright) that exercise the complete system:
real frontend + real server (FastAPI/uvicorn) + real database (SQLite),
all automated by `tests_e2e/conftest.py` - there is no need to open
any extra terminal, start a server manually, or have a pre-existing
database.

## How to run

The official command to run the full suite, 100% automated
with a single command, is:

```
python run_e2e_tests.py
```

It runs each `test_*.py` file in `tests_e2e/` as a **separate** `pytest`
subprocess and prints a summary at the end (how many files
passed/failed), with an exit code != 0 if any fails - ready
for CI pipelines. See the "Known issue" section below for the
reason this script exists instead of running `pytest tests_e2e/ -v`
directly.

### Under the hood

Each file, when run (either through `run_e2e_tests.py` or directly via
`pytest tests_e2e/test_X.py -v`):

1. Creates a temporary, isolated SQLite database (`test_e2e.db`, at the
   project root) - never the real `heredograma.db`, nor the database used by the
   backend tests in `tests/`.
2. Runs `alembic upgrade head` on that database.
3. Runs `seed_perguntas.py` on that database (populates the anamnesis
   question script - required by the tests that answer questions through the UI).
4. Starts the real application (`uvicorn app.main:app`) on port **8001**
   (different from 8000 of the development server, so there is no
   conflict if both are up at the same time).
5. Waits for the server to answer on `/api/status` before running the tests.
6. At the end, stops the server and deletes `test_e2e.db`.

All of this happens inside the `servidor_e2e` fixture (session, autouse) in
`conftest.py` - you do not need to do any of it manually.

## Headless mode (default) vs. visual inspection

By default (and without any extra flag), the tests run with the browser
**headless** (no visible interface) - this is the pytest-playwright default and
what should be used in automatic/CI runs.

If you want to **watch the browser run** (useful to debug a failing
test, or just to follow along visually), run the specific
file with:

```
pytest tests_e2e/test_X.py -v --headed --slowmo 500
```

This is **optional** and not part of the default automatic run.

## Known issue: running `pytest tests_e2e/ -v` directly

Each test file, run on its own, passes reliably. Running ALL the files
together in a single pytest session
(`pytest tests_e2e/ -v`) is currently unstable: starting with the second
complete browser flow of the session (login + registration + consultation), some test
hangs on a navigation, and from then on the server itself (uvicorn) stops
answering other clients too. This was extensively isolated -
it is not caused by SQLite concurrency/slowness, environment CPU throttling, the
navigation strategy (goto vs. click), Playwright context/page
reuse, nor the uvicorn keep-alive timeout
(all of these hypotheses were tested and ruled out in a previous
debugging session). Test environment only - it should not reproduce
in production.

That is why `run_e2e_tests.py` exists: by running each file in its
own `pytest` process (and therefore its own fresh E2E server),
the problem is avoided entirely. Always use `python run_e2e_tests.py`
as the official command; running `pytest tests_e2e/ -v` directly is still available
to run a specific file (`pytest tests_e2e/test_X.py -v`), but
should not be used to run the whole directory at once.

## Writing new tests

- Use the `page` fixture (from pytest-playwright) as usual - relative
  navigations (`page.goto("/pacientes.html")`) already resolve against the
  E2E server's `base_url` automatically.
- Use the `login_admin` fixture to get an administrator professional
  already created (through the API) in this test database, with `email`/`senha`/`token`
  ready - do not assume it already exists.
