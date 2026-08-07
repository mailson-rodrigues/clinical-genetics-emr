from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import obter_profissional_atual
from app.models.anexo import Anexo
from app.models.exame import Exame
from app.models.paciente import Paciente
from app.models.profissional import Profissional
from app.schemas.anexo import AnexoResponse
from app.services import armazenamento

router_pacientes = APIRouter(prefix="/pacientes", tags=["Anexos"])
router_exames = APIRouter(prefix="/exames", tags=["Anexos"])
router_anexos = APIRouter(prefix="/anexos", tags=["Anexos"])


async def _ler_e_validar_arquivo(arquivo: UploadFile) -> bytes:
    if arquivo.content_type not in armazenamento.TIPOS_PERMITIDOS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Tipo de arquivo não permitido: {arquivo.content_type}. "
                f"Tipos aceitos: PDF, JPEG ou PNG."
            ),
        )

    conteudo = await arquivo.read()

    if len(conteudo) > armazenamento.TAMANHO_MAXIMO_BYTES:
        tamanho_mb = armazenamento.TAMANHO_MAXIMO_BYTES / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"Arquivo muito grande. O tamanho máximo permitido é {tamanho_mb:.0f}MB.",
        )

    return conteudo


def _criar_anexo(
    db: Session,
    conteudo: bytes,
    arquivo: UploadFile,
    profissional_id: int,
    paciente_id: int = None,
    exame_id: int = None,
) -> Anexo:
    # Regra de negócio: um Anexo pertence a EXATAMENTE UM de paciente_id
    # ou exame_id - garantido aqui por construção (cada rota chamadora
    # abaixo passa só um dos dois), não pelo banco.
    assert (paciente_id is None) != (exame_id is None), (
        "Anexo deve ter exatamente um de paciente_id/exame_id preenchido."
    )

    nome_armazenado = armazenamento.gerar_nome_armazenado(arquivo.content_type)
    armazenamento.salvar_arquivo(conteudo, nome_armazenado)

    novo = Anexo(
        paciente_id=paciente_id,
        exame_id=exame_id,
        profissional_id=profissional_id,
        nome_original=arquivo.filename,
        nome_armazenado=nome_armazenado,
        tipo_conteudo=arquivo.content_type,
        tamanho_bytes=len(conteudo),
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


# =====================================================================
# Anexos de PACIENTE
# =====================================================================

@router_pacientes.post("/{paciente_id}/anexos", response_model=AnexoResponse, status_code=201)
async def enviar_anexo_paciente(
    paciente_id: int,
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    profissional_atual: Profissional = Depends(obter_profissional_atual),
):
    """Envia um arquivo (documento, laudo, imagem) vinculado a um paciente. Requer login."""
    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")

    conteudo = await _ler_e_validar_arquivo(arquivo)
    return _criar_anexo(db, conteudo, arquivo, profissional_atual.id, paciente_id=paciente_id)


@router_pacientes.get("/{paciente_id}/anexos", response_model=List[AnexoResponse])
def listar_anexos_paciente(
    paciente_id: int,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(obter_profissional_atual),
):
    """Lista os anexos (metadados, não o arquivo em si) de um paciente. Requer login."""
    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")

    return db.query(Anexo).filter(Anexo.paciente_id == paciente_id).order_by(Anexo.criado_em.desc()).all()


# =====================================================================
# Anexos de EXAME
# =====================================================================

@router_exames.post("/{exame_id}/anexos", response_model=AnexoResponse, status_code=201)
async def enviar_anexo_exame(
    exame_id: int,
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    profissional_atual: Profissional = Depends(obter_profissional_atual),
):
    """Envia um arquivo (ex: resultado de exame escaneado) vinculado a um exame. Requer login."""
    exame = db.query(Exame).filter(Exame.id == exame_id).first()
    if not exame:
        raise HTTPException(status_code=404, detail="Exame não encontrado.")

    conteudo = await _ler_e_validar_arquivo(arquivo)
    return _criar_anexo(db, conteudo, arquivo, profissional_atual.id, exame_id=exame_id)


@router_exames.get("/{exame_id}/anexos", response_model=List[AnexoResponse])
def listar_anexos_exame(
    exame_id: int,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(obter_profissional_atual),
):
    """Lista os anexos (metadados, não o arquivo em si) de um exame. Requer login."""
    exame = db.query(Exame).filter(Exame.id == exame_id).first()
    if not exame:
        raise HTTPException(status_code=404, detail="Exame não encontrado.")

    return db.query(Anexo).filter(Anexo.exame_id == exame_id).order_by(Anexo.criado_em.desc()).all()


# =====================================================================
# Download e remoção (por id do anexo, independente de ser de paciente
# ou exame)
# =====================================================================

@router_anexos.get("/{anexo_id}/download")
def baixar_anexo(
    anexo_id: int,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(obter_profissional_atual),
):
    """
    Retorna o arquivo de verdade. NÃO é uma rota pública (dados de
    paciente são sensíveis) - diferente dos arquivos estáticos do
    frontend, este download exige login.
    """
    anexo = db.query(Anexo).filter(Anexo.id == anexo_id).first()
    if not anexo:
        raise HTTPException(status_code=404, detail="Anexo não encontrado.")

    caminho = armazenamento.caminho_completo(anexo.nome_armazenado)
    if not caminho.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado em disco.")

    return FileResponse(path=caminho, media_type=anexo.tipo_conteudo, filename=anexo.nome_original)


@router_anexos.delete("/{anexo_id}", status_code=204)
def remover_anexo(
    anexo_id: int,
    db: Session = Depends(get_db),
    _profissional: Profissional = Depends(obter_profissional_atual),
):
    """Remove o registro do banco E o arquivo físico do disco. Requer login."""
    anexo = db.query(Anexo).filter(Anexo.id == anexo_id).first()
    if not anexo:
        raise HTTPException(status_code=404, detail="Anexo não encontrado.")

    armazenamento.remover_arquivo(anexo.nome_armazenado)
    db.delete(anexo)
    db.commit()
    return None
