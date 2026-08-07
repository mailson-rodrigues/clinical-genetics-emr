import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

from app.schemas.hipotese import HipotesesExtraidas, FonteHipoteseExtraida
from app.services.ia_extracao import montar_texto_anamnese

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Mesmo modelo já usado em ia_extracao.py (extração do heredograma) -
# consistência com o resto do projeto para esse tipo de tarefa
# (extração estruturada a partir de anamnese médica).
MODELO = "claude-sonnet-5"

# Domínios permitidos para a busca na web: PubMed, SciELO, Google
# Acadêmico, OMIM, Orphanet, GARD/NIH, MedlinePlus.
DOMINIOS_PERMITIDOS = [
    "pubmed.ncbi.nlm.nih.gov",
    "ncbi.nlm.nih.gov",
    "scielo.org",
    "scielo.br",
    "scholar.google.com",
    "omim.org",
    "orpha.net",
    "rarediseases.info.nih.gov",
    "medlineplus.gov",
]

FERRAMENTA_BUSCA_WEB = {
    "type": "web_search_20260209",
    "name": "web_search",
    "allowed_domains": DOMINIOS_PERMITIDOS,
    "max_uses": 15,
}

PROMPT_SISTEMA_HIPOTESES = """\
Você é um assistente especializado em aconselhamento genético e
medicina baseada em evidências.

Sua tarefa: ler as perguntas e respostas da anamnese genética de uma
consulta e, usando a ferramenta de busca na web disponível, levantar
hipóteses diagnósticas plausíveis (síndromes genéticas, doenças raras,
predisposições hereditárias) compatíveis com o quadro familiar
descrito.

Ordene a lista de hipóteses da MAIS provável para a MENOS provável,
dado o quadro descrito - a ordem das hipóteses no JSON de resposta
importa e será usada como está.

Regras de busca:
- Use a ferramenta de busca apenas nos domínios já permitidos (PubMed,
  SciELO, Google Acadêmico, OMIM, Orphanet, GARD/NIH, MedlinePlus) -
  não há outros liberados.
- Para CADA hipótese, busque e cite até 5 fontes/artigos que você
  efetivamente consultou nessa pesquisa, priorizando as mais
  diretamente relevantes e recentes. Nunca invente uma fonte - só
  inclua URLs que vieram de verdade dos resultados de busca.

Para cada fonte, preencha:
- "titulo": o título do artigo/página, se disponível (ou null).
- "url": a URL real da página consultada.
- "origem": o nome do site/base de onde veio (ex: "PubMed", "SciELO",
  "OMIM", "Orphanet", "GARD/NIH", "MedlinePlus", "Google Acadêmico").

Para cada hipótese, preencha:
- "condicao": o nome da condição/síndrome (ex: "Síndrome de
  Li-Fraumeni").
- "justificativa": por que essa hipótese é compatível com o quadro
  descrito, em 2-4 frases.
- "cid_sugerido": se você tiver alta confiança no código CID-10
  correspondente a essa condição (ex: "Síndrome de Li-Fraumeni" ->
  "C97"), preencha com esse código. Se não tiver certeza, ou a
  condição não tiver um código CID-10 específico e amplamente aceito,
  deixe como null - não invente um código.
- "fontes": lista de até 5 fontes (ver acima).

Responda APENAS com um JSON válido, sem nenhum texto antes ou depois,
sem markdown, sem crases, no seguinte formato exato:

{
  "hipoteses": [
    {
      "condicao": "string",
      "justificativa": "string",
      "cid_sugerido": "string ou null",
      "fontes": [
        {"titulo": "string ou null", "url": "string", "origem": "string"}
      ]
    }
  ]
}
"""

PROMPT_SISTEMA_MAIS_FONTES = """\
Você é um assistente especializado em aconselhamento genético e
medicina baseada em evidências.

Você já propôs a hipótese diagnóstica descrita a seguir (com
justificativa e fontes já listadas). Sua tarefa agora: usando a
ferramenta de busca na web disponível, encontrar MAIS fontes/artigos
que apoiem essa mesma hipótese - até 5 fontes NOVAS, que não estejam
na lista de fontes já existentes (não repita nenhuma URL já listada).

Regras de busca: as mesmas de sempre - apenas os domínios já
permitidos (PubMed, SciELO, Google Acadêmico, OMIM, Orphanet, GARD/NIH,
MedlinePlus), e nunca invente uma fonte.

Responda APENAS com um JSON válido, sem nenhum texto antes ou depois,
sem markdown, sem crases, no seguinte formato exato:

{
  "fontes": [
    {"titulo": "string ou null", "url": "string", "origem": "string"}
  ]
}
"""


def _extrair_json_da_resposta(resposta):
    if resposta.stop_reason == "max_tokens":
        raise ValueError(
            "A resposta da IA foi cortada por exceder o limite de tokens "
            "configurado (max_tokens). Aumente o valor de max_tokens em "
            "ia_hipoteses.py."
        )
    if resposta.stop_reason == "pause_turn":
        raise ValueError(
            "A pesquisa na web excedeu o número de buscas permitido numa "
            "única requisição. Tente novamente ou reduza max_uses em "
            "ia_hipoteses.py."
        )

    blocos_texto = [bloco for bloco in resposta.content if bloco.type == "text"]
    if not blocos_texto:
        raise ValueError(
            "A resposta da IA não contém nenhum bloco de texto. "
            f"Blocos recebidos: {[bloco.type for bloco in resposta.content]}"
        )
    # Com a ferramenta de busca, a resposta pode ter vários blocos de
    # texto intercalados com as buscas - o JSON final vem sempre no
    # último, depois de toda a pesquisa ter terminado.
    texto_resposta = blocos_texto[-1].text.strip()
    texto_resposta = texto_resposta.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(texto_resposta)
    except json.JSONDecodeError as erro:
        raise ValueError(
            f"A IA não retornou um JSON válido. Resposta recebida:\n{texto_resposta}"
        ) from erro


def gerar_hipoteses(condicao_investigada: str, perguntas_e_respostas: list[dict]) -> HipotesesExtraidas:
    texto_anamnese = montar_texto_anamnese(condicao_investigada, perguntas_e_respostas)

    resposta = client.messages.create(
        model=MODELO,
        max_tokens=8000,
        system=PROMPT_SISTEMA_HIPOTESES,
        tools=[FERRAMENTA_BUSCA_WEB],
        messages=[{"role": "user", "content": texto_anamnese}],
    )

    dados_json = _extrair_json_da_resposta(resposta)
    return HipotesesExtraidas(**dados_json)


def buscar_mais_fontes(
    condicao: str, justificativa: str, fontes_existentes: list[dict]
) -> list[FonteHipoteseExtraida]:
    urls_existentes = "\n".join(f"- {fonte['url']}" for fonte in fontes_existentes) or "(nenhuma ainda)"
    texto_usuario = (
        f"Hipótese: {condicao}\n\n"
        f"Justificativa: {justificativa}\n\n"
        f"Fontes já listadas (não repita):\n{urls_existentes}"
    )

    resposta = client.messages.create(
        model=MODELO,
        max_tokens=4000,
        system=PROMPT_SISTEMA_MAIS_FONTES,
        tools=[FERRAMENTA_BUSCA_WEB],
        messages=[{"role": "user", "content": texto_usuario}],
    )

    dados_json = _extrair_json_da_resposta(resposta)
    return [FonteHipoteseExtraida(**fonte) for fonte in dados_json.get("fontes", [])]
