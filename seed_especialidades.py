"""
Popula o catálogo inicial de especialidades profissionais. Pressupõe
que as tabelas já existem (via Alembic).

Como rodar:
    python seed_especialidades.py
"""

from app.database import SessionLocal
from app.models.profissional import Especialidade

ESPECIALIDADES_INICIAIS = [
    "Geneticista Clínico",
    "Conselheiro Genético",
    "Médico(a) Clínico(a) Geral",
    "Enfermeiro(a)",
    "Biomédico(a)",
    "Psicólogo(a)",
    "Assistente Social",
]


def popular_especialidades():
    db = SessionLocal()
    try:
        inseridas = 0
        for nome in ESPECIALIDADES_INICIAIS:
            ja_existe = db.query(Especialidade).filter(Especialidade.nome == nome).first()
            if not ja_existe:
                db.add(Especialidade(nome=nome))
                inseridas += 1
        db.commit()
        print(f"Concluído. {inseridas} especialidade(s) nova(s) inserida(s).")
    finally:
        db.close()


if __name__ == "__main__":
    popular_especialidades()