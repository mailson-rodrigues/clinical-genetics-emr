"""
Runs the E2E test suite (tests_e2e/) with a single command, executing
EACH test file as a separate pytest subprocess.

Why: running all the files in a single pytest session
(`pytest tests_e2e/ -v`) is currently known to be unstable - see the section
"Known issue" in tests_e2e/README.md. By isolating each file in
its own process, each one starts/stops its own E2E server from
scratch (`servidor_e2e` fixture in tests_e2e/conftest.py), which avoids the
problem entirely - each file, run on its own, passes
reliably.

Usage:
    python run_e2e_tests.py
"""

import subprocess
import sys
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parent
DIRETORIO_E2E = RAIZ_PROJETO / "tests_e2e"


def listar_arquivos_de_teste():
    """All the test_*.py files inside tests_e2e/ (conftest.py is not a test file)."""
    return sorted(DIRETORIO_E2E.glob("test_*.py"))


def rodar_arquivo(caminho):
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(caminho), "-v"],
        cwd=RAIZ_PROJETO,
        capture_output=True,
        text=True,
    )


def main():
    arquivos = listar_arquivos_de_teste()
    if not arquivos:
        print("Nenhum arquivo test_*.py encontrado em tests_e2e/.")
        return 1

    resultados = []
    for arquivo in arquivos:
        nome_relativo = arquivo.relative_to(RAIZ_PROJETO)
        print("=" * 70)
        print(f"Rodando: {nome_relativo}")
        print("=" * 70)

        resultado = rodar_arquivo(arquivo)
        print(resultado.stdout)
        if resultado.stderr:
            print(resultado.stderr)

        resultados.append((nome_relativo, resultado.returncode == 0))
        print()

    print("=" * 70)
    print("RESUMO")
    print("=" * 70)

    total = len(resultados)
    passaram = sum(1 for _, ok in resultados if ok)
    falharam = total - passaram

    for nome, ok in resultados:
        print(f"  [{'PASSOU' if ok else 'FALHOU'}] {nome}")

    print()
    print(f"Total: {total} arquivo(s) - {passaram} passou(aram), {falharam} falhou(aram)")

    return 0 if falharam == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
