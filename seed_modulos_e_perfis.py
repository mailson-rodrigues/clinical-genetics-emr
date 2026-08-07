"""
Popula o catálogo de módulos e os perfis de acesso padrão, e atribui o
perfil mais permissivo (Médico(a)/Geneticista) a profissionais
"profissional" já cadastrados que ainda não têm nenhum perfil - evita
que profissionais existentes percam acesso de repente com a chegada
dos Perfis de Acesso granulares. Administradores não usam perfil
(continuam com acesso total via nivel_acesso == "administrador").

Pressupõe que as tabelas já existem (criadas via Alembic:
`alembic upgrade head`).

Como rodar:
    python seed_modulos_e_perfis.py
"""

from app.database import SessionLocal
from app.models.perfil_acesso import Modulo, PerfilAcesso, PerfilAcessoModulo
from app.models.profissional import Profissional

MODULOS_PADRAO = [
    ("pacientes", "Pacientes"),
    ("consultas", "Consultas e Anamnese"),
    ("historico_clinico", "Histórico Clínico"),
    ("encaminhamentos", "Encaminhamentos"),
    ("exames", "Exames"),
]

PERFIS_PADRAO = {
    "Recepcionista": ["pacientes"],
    "Enfermeiro(a)": ["pacientes", "consultas", "historico_clinico"],
    "Biomédico(a)": ["pacientes", "consultas", "historico_clinico", "exames"],
    "Médico(a)/Geneticista": ["pacientes", "consultas", "historico_clinico", "encaminhamentos", "exames"],
}

PERFIL_PADRAO_PARA_PROFISSIONAIS_EXISTENTES = "Médico(a)/Geneticista"


def popular_modulos(db):
    modulo_por_codigo = {}
    inseridos = 0
    for codigo, nome in MODULOS_PADRAO:
        modulo = db.query(Modulo).filter(Modulo.codigo == codigo).first()
        if not modulo:
            modulo = Modulo(codigo=codigo, nome=nome)
            db.add(modulo)
            db.flush()
            inseridos += 1
        modulo_por_codigo[codigo] = modulo
    db.commit()
    print(f"Módulos: {inseridos} novo(s) inserido(s).")
    return modulo_por_codigo


def popular_perfis(db, modulo_por_codigo):
    perfil_por_nome = {}
    perfis_inseridos = 0
    vinculos_inseridos = 0

    for nome_perfil, codigos_modulos in PERFIS_PADRAO.items():
        perfil = db.query(PerfilAcesso).filter(PerfilAcesso.nome == nome_perfil).first()
        if not perfil:
            perfil = PerfilAcesso(nome=nome_perfil)
            db.add(perfil)
            db.flush()
            perfis_inseridos += 1
        perfil_por_nome[nome_perfil] = perfil

        for codigo in codigos_modulos:
            modulo = modulo_por_codigo[codigo]
            ja_vinculado = db.query(PerfilAcessoModulo).filter(
                PerfilAcessoModulo.perfil_acesso_id == perfil.id,
                PerfilAcessoModulo.modulo_id == modulo.id,
            ).first()
            if not ja_vinculado:
                db.add(PerfilAcessoModulo(perfil_acesso_id=perfil.id, modulo_id=modulo.id))
                vinculos_inseridos += 1

    db.commit()
    print(f"Perfis de acesso: {perfis_inseridos} novo(s) inserido(s). Vínculos: {vinculos_inseridos} novo(s).")
    return perfil_por_nome


def atribuir_perfil_a_profissionais_existentes(db, perfil_por_nome):
    perfil_padrao = perfil_por_nome[PERFIL_PADRAO_PARA_PROFISSIONAIS_EXISTENTES]

    profissionais_sem_perfil = db.query(Profissional).filter(
        Profissional.nivel_acesso == "profissional",
        Profissional.perfil_acesso_id.is_(None),
    ).all()

    for profissional in profissionais_sem_perfil:
        profissional.perfil_acesso_id = perfil_padrao.id

    db.commit()
    print(
        f"Profissionais existentes atualizados com o perfil "
        f"'{PERFIL_PADRAO_PARA_PROFISSIONAIS_EXISTENTES}': {len(profissionais_sem_perfil)}."
    )


def main():
    db = SessionLocal()
    try:
        modulo_por_codigo = popular_modulos(db)
        perfil_por_nome = popular_perfis(db, modulo_por_codigo)
        atribuir_perfil_a_profissionais_existentes(db, perfil_por_nome)
    finally:
        db.close()


if __name__ == "__main__":
    main()
