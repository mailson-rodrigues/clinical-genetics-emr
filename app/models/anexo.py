from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Anexo(Base):
    """
    Arquivo (documento, laudo em PDF, imagem de exame) vinculado a um
    Paciente OU a um Exame - nunca os dois, nunca nenhum (validado na
    rota de criação, não no banco). O arquivo em si fica em disco, em
    uploads/ (fora de frontend/, para não ficar acessível sem
    autenticação via o mount de estáticos) - aqui só os metadados.
    """
    __tablename__ = "anexos"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=True)
    exame_id = Column(Integer, ForeignKey("exames.id"), nullable=True)
    profissional_id = Column(Integer, ForeignKey("profissionais.id"), nullable=True)  # quem enviou

    nome_original = Column(String, nullable=False)  # nome do arquivo, para exibir ao usuário
    nome_armazenado = Column(String, nullable=False)  # uuid4 + extensão, nome real em disco
    tipo_conteudo = Column(String, nullable=False)  # ex: "application/pdf"
    tamanho_bytes = Column(Integer, nullable=False)

    criado_em = Column(DateTime(timezone=True), server_default=func.now())
