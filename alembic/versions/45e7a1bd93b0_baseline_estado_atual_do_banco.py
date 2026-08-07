"""baseline - estado atual do banco

Revision ID: 45e7a1bd93b0
Revises:
Create Date: 2026-07-24 15:10:25.336840

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '45e7a1bd93b0'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Cria o schema inicial do projeto (todas as tabelas anteriores à
    introdução do Alembic).

    NOTA: esta função ficou vazia (`pass`) até 2026-07-25 porque, quando
    esta baseline foi gerada, as tabelas já existiam no heredograma.db
    (criadas direto via Base.metadata.create_all(), antes do Alembic
    entrar no projeto) - então "rodar" a baseline nesse banco não
    precisava fazer nada. Isso passou despercebido até tentarmos rodar
    `alembic upgrade head` num banco NOVO (vazio) do zero - primeiro nos
    testes E2E, mas o mesmo aconteceria em qualquer Postgres de produção
    provisionado hoje: sem essa correção, upgrade head não criaria
    nenhuma tabela. Preencher esta função é seguro para o heredograma.db
    existente, porque essa revisão já está marcada como aplicada nele
    (não roda de novo).
    """
    op.create_table(
        'especialidades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nome'),
    )
    op.create_index(op.f('ix_especialidades_id'), 'especialidades', ['id'], unique=False)

    op.create_table(
        'profissionais',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('senha_hash', sa.String(), nullable=False),
        sa.Column('especialidade_id', sa.Integer(), nullable=True),
        sa.Column('registro_profissional', sa.String(), nullable=True),
        sa.Column('nivel_acesso', sa.String(), nullable=False),
        sa.Column('ativo', sa.Boolean(), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['especialidade_id'], ['especialidades.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_profissionais_id'), 'profissionais', ['id'], unique=False)
    op.create_index(op.f('ix_profissionais_email'), 'profissionais', ['email'], unique=True)

    op.create_table(
        'pacientes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(), nullable=False),
        sa.Column('nome_social', sa.String(), nullable=True),
        sa.Column('data_nascimento', sa.Date(), nullable=False),
        sa.Column('sexo', sa.String(), nullable=False),
        sa.Column('tipo_sanguineo', sa.String(), nullable=True),
        sa.Column('documento', sa.String(), nullable=False),
        sa.Column('rg', sa.String(), nullable=True),
        sa.Column('foto_base64', sa.Text(), nullable=True),
        sa.Column('telefone', sa.String(), nullable=True),
        sa.Column('whatsapp', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('cep', sa.String(), nullable=True),
        sa.Column('endereco', sa.String(), nullable=True),
        sa.Column('numero', sa.String(), nullable=True),
        sa.Column('complemento', sa.String(), nullable=True),
        sa.Column('bairro', sa.String(), nullable=True),
        sa.Column('cidade', sa.String(), nullable=True),
        sa.Column('uf', sa.String(), nullable=True),
        sa.Column('recem_nascido', sa.Boolean(), nullable=True),
        sa.Column('nome_responsavel', sa.String(), nullable=True),
        sa.Column('parentesco_responsavel', sa.String(), nullable=True),
        sa.Column('aceita_mensagens', sa.Boolean(), nullable=True),
        sa.Column('autorizacao_lgpd', sa.Boolean(), nullable=True),
        sa.Column('data_autorizacao_lgpd', sa.DateTime(timezone=True), nullable=True),
        sa.Column('documento_autorizacao_lgpd', sa.String(), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('documento'),
    )
    op.create_index(op.f('ix_pacientes_id'), 'pacientes', ['id'], unique=False)
    op.create_index(op.f('ix_pacientes_documento'), 'pacientes', ['documento'], unique=True)

    op.create_table(
        'perguntas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo', sa.String(), nullable=False),
        sa.Column('categoria', sa.String(), nullable=False),
        sa.Column('texto', sa.Text(), nullable=False),
        sa.Column('ordem', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo'),
    )
    op.create_index(op.f('ix_perguntas_id'), 'perguntas', ['id'], unique=False)
    op.create_index(op.f('ix_perguntas_codigo'), 'perguntas', ['codigo'], unique=True)

    op.create_table(
        'cids',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo', sa.String(), nullable=False),
        sa.Column('descricao', sa.String(), nullable=False),
        sa.Column('capitulo', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo'),
    )
    op.create_index(op.f('ix_cids_id'), 'cids', ['id'], unique=False)
    op.create_index(op.f('ix_cids_codigo'), 'cids', ['codigo'], unique=True)

    op.create_table(
        'operadoras',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nome'),
    )
    op.create_index(op.f('ix_operadoras_id'), 'operadoras', ['id'], unique=False)

    op.create_table(
        'consultas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paciente_id', sa.Integer(), nullable=False),
        sa.Column('profissional_id', sa.Integer(), nullable=True),
        sa.Column('condicao_investigada', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['paciente_id'], ['pacientes.id']),
        sa.ForeignKeyConstraint(['profissional_id'], ['profissionais.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_consultas_id'), 'consultas', ['id'], unique=False)

    op.create_table(
        'respostas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('consulta_id', sa.Integer(), nullable=False),
        sa.Column('pergunta_id', sa.Integer(), nullable=False),
        sa.Column('resposta_texto', sa.Text(), nullable=False),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['consulta_id'], ['consultas.id']),
        sa.ForeignKeyConstraint(['pergunta_id'], ['perguntas.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_respostas_id'), 'respostas', ['id'], unique=False)

    op.create_table(
        'individuos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('consulta_id', sa.Integer(), nullable=False),
        sa.Column('codigo', sa.String(), nullable=False),
        sa.Column('geracao', sa.Integer(), nullable=False),
        sa.Column('posicao', sa.Integer(), nullable=False),
        sa.Column('papel_descricao', sa.String(), nullable=True),
        sa.Column('observacao', sa.Text(), nullable=True),
        sa.Column('sexo', sa.String(), nullable=False),
        sa.Column('afetado', sa.Boolean(), nullable=True),
        sa.Column('portador', sa.Boolean(), nullable=True),
        sa.Column('falecido', sa.Boolean(), nullable=True),
        sa.Column('probando', sa.Boolean(), nullable=True),
        sa.Column('cid_sugerido', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['consulta_id'], ['consultas.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_individuos_id'), 'individuos', ['id'], unique=False)

    op.create_table(
        'relacionamentos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('consulta_id', sa.Integer(), nullable=False),
        sa.Column('tipo', sa.String(), nullable=False),
        sa.Column('origem_codigo', sa.String(), nullable=False),
        sa.Column('destino_codigo', sa.String(), nullable=False),
        sa.Column('consanguineo', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['consulta_id'], ['consultas.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_relacionamentos_id'), 'relacionamentos', ['id'], unique=False)

    op.create_table(
        'alergias',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paciente_id', sa.Integer(), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['paciente_id'], ['pacientes.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_alergias_id'), 'alergias', ['id'], unique=False)

    op.create_table(
        'doencas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paciente_id', sa.Integer(), nullable=False),
        sa.Column('cid_id', sa.Integer(), nullable=True),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['cid_id'], ['cids.id']),
        sa.ForeignKeyConstraint(['paciente_id'], ['pacientes.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_doencas_id'), 'doencas', ['id'], unique=False)

    op.create_table(
        'cirurgias',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paciente_id', sa.Integer(), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['paciente_id'], ['pacientes.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_cirurgias_id'), 'cirurgias', ['id'], unique=False)

    op.create_table(
        'historicos_clinicos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paciente_id', sa.Integer(), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['paciente_id'], ['pacientes.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_historicos_clinicos_id'), 'historicos_clinicos', ['id'], unique=False)

    op.create_table(
        'paciente_convenios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paciente_id', sa.Integer(), nullable=False),
        sa.Column('operadora_id', sa.Integer(), nullable=False),
        sa.Column('numero_carteirinha', sa.String(), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['operadora_id'], ['operadoras.id']),
        sa.ForeignKeyConstraint(['paciente_id'], ['pacientes.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_paciente_convenios_id'), 'paciente_convenios', ['id'], unique=False)

    op.create_table(
        'logs_auditoria',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profissional_id', sa.Integer(), nullable=True),
        sa.Column('metodo', sa.String(), nullable=False),
        sa.Column('caminho', sa.String(), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['profissional_id'], ['profissionais.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_logs_auditoria_id'), 'logs_auditoria', ['id'], unique=False)


def downgrade() -> None:
    """Reverte o schema inicial (ordem inversa da criação, por causa das FKs)."""
    op.drop_index(op.f('ix_logs_auditoria_id'), table_name='logs_auditoria')
    op.drop_table('logs_auditoria')

    op.drop_index(op.f('ix_paciente_convenios_id'), table_name='paciente_convenios')
    op.drop_table('paciente_convenios')

    op.drop_index(op.f('ix_historicos_clinicos_id'), table_name='historicos_clinicos')
    op.drop_table('historicos_clinicos')

    op.drop_index(op.f('ix_cirurgias_id'), table_name='cirurgias')
    op.drop_table('cirurgias')

    op.drop_index(op.f('ix_doencas_id'), table_name='doencas')
    op.drop_table('doencas')

    op.drop_index(op.f('ix_alergias_id'), table_name='alergias')
    op.drop_table('alergias')

    op.drop_index(op.f('ix_relacionamentos_id'), table_name='relacionamentos')
    op.drop_table('relacionamentos')

    op.drop_index(op.f('ix_individuos_id'), table_name='individuos')
    op.drop_table('individuos')

    op.drop_index(op.f('ix_respostas_id'), table_name='respostas')
    op.drop_table('respostas')

    op.drop_index(op.f('ix_consultas_id'), table_name='consultas')
    op.drop_table('consultas')

    op.drop_index(op.f('ix_operadoras_id'), table_name='operadoras')
    op.drop_table('operadoras')

    op.drop_index(op.f('ix_cids_codigo'), table_name='cids')
    op.drop_index(op.f('ix_cids_id'), table_name='cids')
    op.drop_table('cids')

    op.drop_index(op.f('ix_perguntas_codigo'), table_name='perguntas')
    op.drop_index(op.f('ix_perguntas_id'), table_name='perguntas')
    op.drop_table('perguntas')

    op.drop_index(op.f('ix_pacientes_documento'), table_name='pacientes')
    op.drop_index(op.f('ix_pacientes_id'), table_name='pacientes')
    op.drop_table('pacientes')

    op.drop_index(op.f('ix_profissionais_email'), table_name='profissionais')
    op.drop_index(op.f('ix_profissionais_id'), table_name='profissionais')
    op.drop_table('profissionais')

    op.drop_index(op.f('ix_especialidades_id'), table_name='especialidades')
    op.drop_table('especialidades')
