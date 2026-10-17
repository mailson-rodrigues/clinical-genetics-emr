"""
Runs the WHOLE test suite of the project (backend + end-to-end) with a
single command, and prints a clear overall summary at the end - without having to
run `pytest tests/` and `run_e2e_tests.py` separately nor interpret
two different outputs.

Usage:
    python executar_todos_os_testes.py
"""

import re
import subprocess
import sys
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parent

PADRAO_CONTAGEM_PYTEST = re.compile(r"(\d+)\s+(passed|failed|errors?|skipped|xfailed|xpassed)\b")
PADRAO_RESUMO_E2E = re.compile(
    r"Total:\s*(\d+)\s*arquivo\(s\)\s*-\s*(\d+)\s*passou\(aram\),\s*(\d+)\s*falhou\(aram\)"
)


def rodar(comando):
    return subprocess.run(comando, cwd=RAIZ_PROJETO, capture_output=True, text=True)


def extrair_ultima_linha_de_resumo_pytest(saida):
    """
    Searches, from the bottom up, for the last line of the pytest output that
    contains recognizable counts (e.g. "51 passed, 17 warnings in
    49.60s" or "2 failed, 63 passed in 60.85s"). Returns the raw line,
    or None if none is found.
    """
    for linha in reversed(saida.strip().splitlines()):
        if PADRAO_CONTAGEM_PYTEST.search(linha):
            return linha
    return None


def formatar_resumo_backend(resultado):
    """
    Extracts a short summary (e.g. "70 passed") from the pytest output via a
    simple regex - if it cannot recognize the format, returns None
    (the caller shows the raw output instead of inventing a number).
    """
    linha_resumo = extrair_ultima_linha_de_resumo_pytest(resultado.stdout)
    if linha_resumo is None:
        return None

    contagens = {}
    for numero, rotulo in PADRAO_CONTAGEM_PYTEST.findall(linha_resumo):
        chave = "error" if rotulo.startswith("error") else rotulo
        contagens[chave] = contagens.get(chave, 0) + int(numero)

    partes = [f"{quantidade} {rotulo}" for rotulo, quantidade in contagens.items()]
    return ", ".join(partes) if partes else linha_resumo.strip()


def formatar_resumo_e2e(resultado):
    """
    Extracts the summary (e.g. "5/5 file(s) passed") from the final line that
    run_e2e_tests.py always prints - if the format changes and does not match
    the regex, returns None.
    """
    correspondencia = PADRAO_RESUMO_E2E.search(resultado.stdout)
    if not correspondencia:
        return None

    total, passaram, falharam = correspondencia.groups()
    resumo = f"{passaram}/{total} arquivo(s) passaram"
    if int(falharam) > 0:
        resumo += f", {falharam} falharam"
    return resumo


def imprimir_saida_completa(titulo, resultado):
    print()
    print("=" * 70)
    print(titulo)
    print("=" * 70)
    print(resultado.stdout)
    if resultado.stderr:
        print(resultado.stderr)


def main():
    print("Rodando testes de backend (pytest tests/)...")
    resultado_backend = rodar([sys.executable, "-m", "pytest", "tests/", "-v"])
    backend_ok = resultado_backend.returncode == 0

    print("Rodando testes end-to-end (python run_e2e_tests.py)...")
    resultado_e2e = rodar([sys.executable, "run_e2e_tests.py"])
    e2e_ok = resultado_e2e.returncode == 0

    # The full output is only shown for groups that failed - keeps the
    # "everything passed" case short and to the point, but never hides
    # diagnostic information when something goes wrong.
    if not backend_ok:
        imprimir_saida_completa("SAÍDA COMPLETA - BACKEND (pytest tests/) - FALHOU", resultado_backend)
    if not e2e_ok:
        imprimir_saida_completa("SAÍDA COMPLETA - END-TO-END (run_e2e_tests.py) - FALHOU", resultado_e2e)

    resumo_backend = formatar_resumo_backend(resultado_backend)
    resumo_e2e = formatar_resumo_e2e(resultado_e2e)

    texto_backend = resumo_backend or "não foi possível interpretar a saída - ver acima"
    texto_e2e = resumo_e2e or "não foi possível interpretar a saída - ver acima"

    linha_backend = f"{'OK' if backend_ok else 'FALHOU'} - {texto_backend}"
    linha_e2e = f"{'OK' if e2e_ok else 'FALHOU'} - {texto_e2e}"

    print()
    print("=" * 50)
    print("RESUMO GERAL DOS TESTES")
    print("=" * 50)
    print(f"Backend (pytest):        {linha_backend}")
    print(f"End-to-end (Playwright): {linha_e2e}")
    print("=" * 50)

    tudo_passou = backend_ok and e2e_ok
    if tudo_passou:
        print("RESULTADO FINAL: TUDO PASSOU")
    else:
        grupos_com_falha = []
        if not backend_ok:
            grupos_com_falha.append("backend")
        if not e2e_ok:
            grupos_com_falha.append("end-to-end")
        print(f"RESULTADO FINAL: FALHOU ({', '.join(grupos_com_falha)}) - ver saída completa acima")
    print("=" * 50)

    return 0 if tudo_passou else 1


if __name__ == "__main__":
    sys.exit(main())
