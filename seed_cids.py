"""
Script para popular o catálogo de códigos CID-10 com uma lista curada
de exemplo. Pressupõe que as tabelas já existem (via Alembic).

Como rodar:
    python seed_cids.py
"""

from app.database import SessionLocal
from app.models.cid import Cid

CIDS_INICIAIS = [
    ("C50", "Neoplasia maligna da mama", "Neoplasias"),
    ("C61", "Neoplasia maligna da próstata", "Neoplasias"),
    ("C56", "Neoplasia maligna do ovário", "Neoplasias"),
    ("C34", "Neoplasia maligna dos brônquios e do pulmão", "Neoplasias"),
    ("C18", "Neoplasia maligna do cólon", "Neoplasias"),
    ("C25", "Neoplasia maligna do pâncreas", "Neoplasias"),
    ("C64", "Neoplasia maligna do rim, exceto pelve renal", "Neoplasias"),
    ("C73", "Neoplasia maligna da glândula tireoide", "Neoplasias"),
    ("C22", "Neoplasia maligna do fígado e vias biliares intra-hepáticas", "Neoplasias"),
    ("C43", "Melanoma maligno da pele", "Neoplasias"),
    ("Q90", "Síndrome de Down", "Malformações congênitas, deformidades e anomalias cromossômicas"),
    ("Q91", "Síndrome de Edwards e síndrome de Patau", "Malformações congênitas, deformidades e anomalias cromossômicas"),
    ("Q99", "Outras anomalias dos cromossomos, não classificadas em outra parte", "Malformações congênitas, deformidades e anomalias cromossômicas"),
    ("E84", "Fibrose cística", "Doenças endócrinas, nutricionais e metabólicas"),
    ("E70", "Distúrbios do metabolismo de aminoácidos aromáticos", "Doenças endócrinas, nutricionais e metabólicas"),
    ("D56", "Talassemia", "Doenças do sangue e dos órgãos hematopoéticos"),
    ("D57", "Transtornos falciformes", "Doenças do sangue e dos órgãos hematopoéticos"),
    ("G71", "Transtornos primários dos músculos (distrofias musculares)", "Doenças do sistema nervoso"),
    ("Q78", "Outras osteocondrodisplasias (inclui osteogênese imperfeita)", "Malformações congênitas, deformidades e anomalias cromossômicas"),
    ("I42", "Cardiomiopatia", "Doenças do aparelho circulatório"),
    ("E10", "Diabetes mellitus insulino-dependente", "Doenças endócrinas, nutricionais e metabólicas"),
    ("E11", "Diabetes mellitus não-insulino-dependente", "Doenças endócrinas, nutricionais e metabólicas"),
    ("I10", "Hipertensão essencial (primária)", "Doenças do aparelho circulatório"),
    ("N18", "Doença renal crônica", "Doenças do aparelho geniturinário"),
]


def popular_cids():
    db = SessionLocal()
    try:
        inseridos = 0
        for codigo, descricao, capitulo in CIDS_INICIAIS:
            ja_existe = db.query(Cid).filter(Cid.codigo == codigo).first()
            if not ja_existe:
                db.add(Cid(codigo=codigo, descricao=descricao, capitulo=capitulo))
                inseridos += 1
        db.commit()
        print(f"Concluído. {inseridos} código(s) CID novo(s) inserido(s).")
    finally:
        db.close()


if __name__ == "__main__":
    popular_cids()