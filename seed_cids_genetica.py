"""
Script para expandir o catálogo de códigos CID-10 com códigos de
genética/doenças raras/oncologia hereditária. Pressupõe que as tabelas
já existem (via Alembic) - complementa seed_cids.py, sem duplicar
códigos já cadastrados.

Como rodar:
    python seed_cids_genetica.py
"""

from app.database import SessionLocal
from app.models.cid import Cid

CODIGOS_GENETICA_RARAS_ONCOLOGIA = [
    ("C16", "Neoplasia maligna do estômago", "Neoplasias"),
    ("C54", "Neoplasia maligna do corpo do útero", "Neoplasias"),
    ("C69.2", "Neoplasia maligna da retina (retinoblastoma)", "Neoplasias"),
    ("C74.1", "Neoplasia maligna da medula da suprarrenal (feocromocitoma)", "Neoplasias"),
    ("C91", "Leucemia linfoide", "Neoplasias"),
    ("C92", "Leucemia mieloide", "Neoplasias"),
    ("D44", "Neoplasia de comportamento incerto das glândulas endócrinas", "Neoplasias"),
    ("E74.0", "Doenças de depósito de glicogênio", "Doenças endócrinas, nutricionais e metabólicas"),
    ("E74.2", "Distúrbios do metabolismo da galactose (galactosemia)", "Doenças endócrinas, nutricionais e metabólicas"),
    ("E75.0", "Gangliosidose GM2 (Tay-Sachs)", "Doenças endócrinas, nutricionais e metabólicas"),
    ("E75.2", "Outras esfingolipidoses (Gaucher, Niemann-Pick)", "Doenças endócrinas, nutricionais e metabólicas"),
    ("E76", "Distúrbios do metabolismo dos glicosaminoglicanos (mucopolissacaridoses)", "Doenças endócrinas, nutricionais e metabólicas"),
    ("E78.0", "Hipercolesterolemia pura familiar", "Doenças endócrinas, nutricionais e metabólicas"),
    ("E83.0", "Distúrbios do metabolismo do cobre (doença de Wilson)", "Doenças endócrinas, nutricionais e metabólicas"),
    ("E83.1", "Distúrbios do metabolismo do ferro (hemocromatose)", "Doenças endócrinas, nutricionais e metabólicas"),
    ("D55.0", "Anemia devida a deficiência de G6PD", "Doenças do sangue e dos órgãos hematopoéticos"),
    ("D66", "Deficiência hereditária do fator VIII (hemofilia A)", "Doenças do sangue e dos órgãos hematopoéticos"),
    ("D67", "Deficiência hereditária do fator IX (hemofilia B)", "Doenças do sangue e dos órgãos hematopoéticos"),
    ("G10", "Doença de Huntington", "Doenças do sistema nervoso"),
    ("G11", "Ataxia hereditária", "Doenças do sistema nervoso"),
    ("G12.0", "Atrofia muscular espinhal infantil tipo I", "Doenças do sistema nervoso"),
    ("G12.1", "Outras atrofias musculares espinhais hereditárias", "Doenças do sistema nervoso"),
    ("G60.0", "Neuropatia hereditária motora e sensitiva (Charcot-Marie-Tooth)", "Doenças do sistema nervoso"),
    ("G71.1", "Distrofias miotônicas", "Doenças do sistema nervoso"),
    ("Q05", "Espinha bífida", "Malformações congênitas, deformidades e anomalias cromossômicas"),
    ("Q35", "Fenda palatina", "Malformações congênitas, deformidades e anomalias cromossômicas"),
    ("Q36", "Fenda labial (lábio leporino)", "Malformações congênitas, deformidades e anomalias cromossômicas"),
    ("Q69", "Polidactilia", "Malformações congênitas, deformidades e anomalias cromossômicas"),
    ("Q80", "Ictiose congênita", "Malformações congênitas, deformidades e anomalias cromossômicas"),
    ("Q81", "Epidermólise bolhosa", "Malformações congênitas, deformidades e anomalias cromossômicas"),
    ("Q82.1", "Xeroderma pigmentoso", "Malformações congênitas, deformidades e anomalias cromossômicas"),
    ("Q85.1", "Esclerose tuberosa", "Malformações congênitas, deformidades e anomalias cromossômicas"),
    ("Q85.8", "Outras facomatoses (Von Hippel-Lindau)", "Malformações congênitas, deformidades e anomalias cromossômicas"),
    ("Q87.4", "Síndrome de Marfan", "Malformações congênitas, deformidades e anomalias cromossômicas"),
    ("Q96", "Síndrome de Turner", "Malformações congênitas, deformidades e anomalias cromossômicas"),
    ("Q98", "Outras anomalias dos cromossomos sexuais (Klinefelter)", "Malformações congênitas, deformidades e anomalias cromossômicas"),
    ("Z80.0", "História familiar de neoplasia maligna do aparelho digestivo", "Fatores que influenciam o estado de saúde e o contato com serviços de saúde"),
    ("Z80.3", "História familiar de neoplasia maligna da mama", "Fatores que influenciam o estado de saúde e o contato com serviços de saúde"),
    ("Z80.4", "História familiar de neoplasia maligna dos órgãos genitais", "Fatores que influenciam o estado de saúde e o contato com serviços de saúde"),
    ("Z80.8", "História familiar de neoplasia maligna de outros órgãos", "Fatores que influenciam o estado de saúde e o contato com serviços de saúde"),
    ("Z82.0", "História familiar de epilepsia e outras doenças do sistema nervoso", "Fatores que influenciam o estado de saúde e o contato com serviços de saúde"),
    ("Z82.5", "História familiar de cegueira e perda da visão", "Fatores que influenciam o estado de saúde e o contato com serviços de saúde"),
    ("Z82.7", "História familiar de malformações, deformidades e anomalias cromossômicas", "Fatores que influenciam o estado de saúde e o contato com serviços de saúde"),
    ("Z83.4", "História familiar de outros distúrbios endócrinos e metabólicos", "Fatores que influenciam o estado de saúde e o contato com serviços de saúde"),
    ("Z84.0", "História familiar de doenças do rim e do ureter", "Fatores que influenciam o estado de saúde e o contato com serviços de saúde"),
]


def popular_cids_genetica():
    db = SessionLocal()
    try:
        inseridos = 0
        for codigo, descricao, capitulo in CODIGOS_GENETICA_RARAS_ONCOLOGIA:
            ja_existe = db.query(Cid).filter(Cid.codigo == codigo).first()
            if not ja_existe:
                db.add(Cid(codigo=codigo, descricao=descricao, capitulo=capitulo, versao="CID-10"))
                inseridos += 1
        db.commit()
        print(f"Concluído. {inseridos} código(s) CID novo(s) inserido(s).")
    finally:
        db.close()


if __name__ == "__main__":
    popular_cids_genetica()
