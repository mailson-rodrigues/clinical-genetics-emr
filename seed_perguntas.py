"""
Script para popular o banco com o roteiro padrão de perguntas de anamnese
genética. Pressupõe que as tabelas já existem (criadas via Alembic:
`alembic upgrade head`).

Como rodar:
    python seed_perguntas.py
"""

from app.database import SessionLocal
from app.models.anamnese import Pergunta

ROTEIRO_PADRAO = [
    ("CONDICAO_DESCRICAO", "Condição investigada", "Descreva a característica ou doença que motivou a consulta.", 1),
    ("CONDICAO_MODO_HERANCA", "Condição investigada", "Já se sabe o modo de herança (dominante, recessivo, ligado ao X)?", 2),
    ("PACIENTE_AFETADO", "Paciente", "O(a) paciente apresenta a característica/doença investigada?", 3),
    ("PACIENTE_SEXO", "Paciente", "Sexo biológico do paciente.", 4),
    ("PAI_VIVO", "Pais", "O pai do paciente é vivo?", 5),
    ("PAI_AFETADO", "Pais", "O pai apresenta a característica/doença investigada?", 6),
    ("MAE_VIVA", "Pais", "A mãe do paciente é viva?", 7),
    ("MAE_AFETADA", "Pais", "A mãe apresenta a característica/doença investigada?", 8),
    ("PAIS_CONSANGUINEOS", "Pais", "Há consanguinidade entre o pai e a mãe (parentesco entre eles)?", 9),
    ("IRMAOS_QTD", "Irmãos", "Quantos irmãos o paciente tem?", 10),
    ("IRMAOS_AFETADOS", "Irmãos", "Algum irmão apresenta a característica/doença investigada? Quais e qual o sexo?", 11),
    ("AVO_MATERNA_AFETADA", "Avós", "A avó materna apresenta/apresentava a característica/doença?", 12),
    ("AVO_MATERNO_AFETADO", "Avós", "O avô materno apresenta/apresentava a característica/doença?", 13),
    ("AVO_PATERNA_AFETADA", "Avós", "A avó paterna apresenta/apresentava a característica/doença?", 14),
    ("AVO_PATERNO_AFETADO", "Avós", "O avô paterno apresenta/apresentava a característica/doença?", 15),
    ("FILHOS_QTD", "Filhos", "O paciente tem filhos? Quantos?", 16),
    ("FILHOS_AFETADOS", "Filhos", "Algum filho apresenta a característica/doença investigada? Quais e qual o sexo?", 17),
    ("OUTROS_PARENTES", "Outros parentes", "Há outros parentes (tios, primos) com a característica/doença investigada? Descreva o parentesco.", 18),
    ("OBITOS_RELACIONADOS", "Histórico", "Houve óbitos na família relacionados à condição investigada? Descreva.", 19),
]


def popular_perguntas():
    db = SessionLocal()
    try:
        inseridas = 0
        for codigo, categoria, texto, ordem in ROTEIRO_PADRAO:
            ja_existe = db.query(Pergunta).filter(Pergunta.codigo == codigo).first()
            if not ja_existe:
                db.add(Pergunta(codigo=codigo, categoria=categoria, texto=texto, ordem=ordem))
                inseridas += 1
        db.commit()
        print(f"Concluído. {inseridas} pergunta(s) nova(s) inserida(s).")
    finally:
        db.close()


if __name__ == "__main__":
    popular_perguntas()