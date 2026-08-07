"""
Roda a suíte de testes E2E (tests_e2e/) com um único comando, executando
CADA arquivo de teste como um subprocesso pytest separado.

Por quê: rodar todos os arquivos numa única sessão do pytest
(`pytest tests_e2e/ -v`) é sabidamente instável hoje - ver a seção
"Problema conhecido" em tests_e2e/README.md. Isolando cada arquivo em
seu próprio processo, cada um sobe/derruba seu próprio servidor E2E do
zero (fixture `servidor_e2e` em tests_e2e/conftest.py), o que evita o
problema por completo - cada arquivo, rodado sozinho, passa de forma
confiável.

Uso:
    python run_e2e_tests.py
"""

import subprocess
import sys
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parent
DIRETORIO_E2E = RAIZ_PROJETO / "tests_e2e"


def listar_arquivos_de_teste():
    """Todos os test_*.py dentro de tests_e2e/ (conftest.py não é um arquivo de teste)."""
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
