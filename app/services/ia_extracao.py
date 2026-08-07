import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

from app.schemas.heredograma import HeredogramaExtraido

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MODELO = "claude-sonnet-5"

PROMPT_SISTEMA = """\
Você é um assistente especializado em genética médica e heredogramas
(pedigrees), seguindo o padrão internacional de nomenclatura do
Pedigree Standardization Task Force (PSTF) da National Society of
Genetic Counselors (NSGC).

Sua tarefa: ler as perguntas e respostas de uma anamnese de
aconselhamento genético e extrair os indivíduos da família e as
relações entre eles, para construção de um heredograma.

Regras de codificação:
- Cada indivíduo recebe um código no formato "GERACAO.POSICAO",
  ex: "I.1", "I.2", "II.1", "II.2". A geração mais antiga citada
  (avós) é a geração I; os pais são a geração II; o(a) paciente e
  seus irmãos são a geração III; os filhos do paciente são a
  geração IV. Ajuste as gerações conforme o que for citado.
- O paciente da consulta é o "probando" (probando=true).
- sexo deve ser exatamente "M", "F" ou "Desconhecido".
- Se uma informação não foi mencionada, não invente: use valores
  padrão neutros (afetado=false, portador=false, falecido=false) e
  não crie indivíduos que não foram citados.

Regras MUITO IMPORTANTES sobre os campos "papel_descricao" e "observacao"
(são campos SEPARADOS, nunca misture um dentro do outro):
- "papel_descricao": APENAS o papel/relação familiar da pessoa, de forma
  curta e padronizada. Exemplos corretos: "Pai", "Mãe", "Avô paterno",
  "Avó materna", "Irmã", "Meia-irmã (mesma mãe: II.3)", "Paciente",
  "Tio materno", "Primo de primeiro grau". NUNCA inclua informação
  clínica (diagnóstico, exame, status de investigação) neste campo.
- "observacao": informação clínica ADICIONAL relevante mencionada nas
  respostas, de forma breve (ideal até ~40 caracteres). Exemplos:
  "PSA alterado, em investigação", "Câncer de próstata aos 68 anos",
  "Cirurgia cardíaca em 2020". Se não houver informação clínica
  adicional relevante além do já capturado em afetado/falecido/etc,
  deixe "observacao" como null - não repita o que já está nos outros
  campos booleanos.

Exemplo CORRETO:
  "papel_descricao": "Pai"
  "observacao": "PSA alterado, em investigação"

Exemplo INCORRETO (não faça isso):
  "papel_descricao": "Pai - PSA alterado, em investigação"
  "observacao": null

- Toda relação de casal (pais entre si, avós entre si) deve gerar
  um relacionamento tipo "uniao".
- Toda relação de filiação (pai->filho e mãe->filho) deve gerar
  DOIS relacionamentos tipo "filiacao" (um para cada genitor),
  quando ambos os genitores forem conhecidos. Se só um genitor foi
  citado, gere apenas um.
- Consanguinidade entre pais deve ser marcada com consanguineo=true
  no relacionamento tipo "uniao" correspondente.
- Quando um indivíduo for descrito como afetado por uma condição/
  doença específica e você tiver alta confiança no código CID-10
  correspondente (ex: "câncer de próstata" -> "C61"), preencha o
  campo "cid_sugerido" com esse código. Se não tiver certeza, ou a
  condição for vaga/genérica, deixe "cid_sugerido" como null.

Responda APENAS com um JSON válido, sem nenhum texto antes ou depois,
sem markdown, sem crases, no seguinte formato exato:

{
  "individuos": [
    {
      "codigo": "string",
      "geracao": int,
      "posicao": int,
      "papel_descricao": "string ou null",
      "observacao": "string ou null",
      "sexo": "M" | "F" | "Desconhecido",
      "afetado": bool,
      "portador": bool,
      "falecido": bool,
      "probando": bool,
      "cid_sugerido": "string ou null"
    }
  ],
  "relacionamentos": [
    {
      "tipo": "uniao" | "filiacao",
      "origem_codigo": "string",
      "destino_codigo": "string",
      "consanguineo": bool
    }
  ]
}
"""


def montar_texto_anamnese(condicao_investigada: str, perguntas_e_respostas: list[dict]) -> str:
    linhas = [f"Condição investigada: {condicao_investigada}", ""]
    categoria_atual = None
    for item in perguntas_e_respostas:
        if item["categoria"] != categoria_atual:
            categoria_atual = item["categoria"]
            linhas.append(f"\n## {categoria_atual}")
        linhas.append(f"P: {item['pergunta']}")
        linhas.append(f"R: {item['resposta']}")
    return "\n".join(linhas)


def extrair_heredograma(condicao_investigada: str, perguntas_e_respostas: list[dict]) -> HeredogramaExtraido:
    texto_anamnese = montar_texto_anamnese(condicao_investigada, perguntas_e_respostas)

    resposta = client.messages.create(
        model=MODELO,
        max_tokens=8000,
        system=PROMPT_SISTEMA,
        messages=[
            {"role": "user", "content": texto_anamnese}
        ],
    )

    if resposta.stop_reason == "max_tokens":
        raise ValueError(
            "A resposta da IA foi cortada por exceder o limite de tokens "
            "configurado (max_tokens). Isso costuma acontecer em famílias "
            "muito grandes/complexas. Aumente o valor de max_tokens em "
            "ia_extracao.py, ou simplifique a anamnese."
        )

    bloco_texto = next(
        (bloco for bloco in resposta.content if bloco.type == "text"),
        None
    )
    if bloco_texto is None:
        raise ValueError(
            "A resposta da IA não contém nenhum bloco de texto. "
            f"Blocos recebidos: {[bloco.type for bloco in resposta.content]}"
        )
    texto_resposta = bloco_texto.text.strip()

    texto_resposta = texto_resposta.replace("```json", "").replace("```", "").strip()

    try:
        dados_json = json.loads(texto_resposta)
    except json.JSONDecodeError as erro:
        raise ValueError(
            f"A IA não retornou um JSON válido. Resposta recebida:\n{texto_resposta}"
        ) from erro

    heredograma_validado = HeredogramaExtraido(**dados_json)
    return heredograma_validado