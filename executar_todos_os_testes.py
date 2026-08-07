"""
Roda TODA a suíte de testes do projeto (backend + end-to-end) com um
único comando, e imprime um resumo geral claro ao final - sem precisar
rodar `pytest tests/` e `run_e2e_tests.py` separadamente nem interpretar
duas saídas diferentes.

Uso:
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
    Procura, de baixo para cima, a última linha da saída do pytest que
    contém contagens reconhecíveis (ex: "51 passed, 17 warnings in
    49.60s" ou "2 failed, 63 passed in 60.85s"). Retorna a linha bruta,
    ou None se não encontrar nenhuma.
    """
    for linha in reversed(saida.strip().splitlines()):
        if PADRAO_CONTAGEM_PYTEST.search(linha):
            return linha
    return None


def formatar_resumo_backend(resultado):
    """
    Extrai um resumo curto (ex: "70 passed") da saída do pytest via
    regex simples - se não conseguir reconhecer o formato, devolve None
    (quem chama mostra a saída bruta em vez de inventar um número).
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
    Extrai o resumo (ex: "5/5 arquivo(s) passaram") da linha final que
    run_e2e_tests.py sempre imprime - se o formato mudar e não bater
    com o regex, devolve None.
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

    # Saída completa só é exibida para grupos que falharam - mantém o
    # caso "tudo passou" curto e direto ao ponto, mas nunca esconde
    # informação de diagnóstico quando algo dá errado.
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
