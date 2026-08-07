// =====================================================================
// CONFIGURAÇÕES DE LAYOUT
// =====================================================================
const COL_WIDTH = 160;
const ROW_HEIGHT = 200;
const MARGIN_X = 90;
const MARGIN_Y = 70;
const TAMANHO_SIMBOLO = 24;
const ALTURA_LINHA_TEXTO = 12;

function criarElementoSVG(tag, atributos = {}) {
  const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [chave, valor] of Object.entries(atributos)) {
    el.setAttribute(chave, valor);
  }
  return el;
}

// =====================================================================
// PASSO 1: BUSCAR OS DADOS DA API
// =====================================================================
async function buscarHeredograma(consultaId) {
  const resposta = await fetch(`/consultas/${consultaId}/heredograma`);
  if (!resposta.ok) {
    const erro = await resposta.json().catch(() => ({}));
    throw new Error(erro.detail || `Erro HTTP ${resposta.status}`);
  }
  return resposta.json();
}

function construirParceirosPorCodigo(relacionamentos) {
  const parceirosPorCodigo = {};
  relacionamentos
    .filter((r) => r.tipo === "uniao")
    .forEach((u) => {
      if (!parceirosPorCodigo[u.origem_codigo]) parceirosPorCodigo[u.origem_codigo] = [];
      if (!parceirosPorCodigo[u.destino_codigo]) parceirosPorCodigo[u.destino_codigo] = [];
      parceirosPorCodigo[u.origem_codigo].push(u.destino_codigo);
      parceirosPorCodigo[u.destino_codigo].push(u.origem_codigo);
    });
  return parceirosPorCodigo;
}

function ajustarAdjacenciaConjuges(ordemOriginal, parceirosPorCodigo, porCodigo, geracao) {
  const resultado = [];
  const usados = new Set();

  for (const codigo of ordemOriginal) {
    if (usados.has(codigo)) continue;

    const parceiros = (parceirosPorCodigo[codigo] || []).filter(
      (p) => porCodigo[p] && porCodigo[p].geracao === geracao && !usados.has(p)
    );

    const antes = [];
    const depois = [];
    parceiros.forEach((parceiro, indice) => {
      if (indice % 2 === 0) depois.push(parceiro);
      else antes.push(parceiro);
    });

    antes.forEach((p) => { resultado.push(p); usados.add(p); });
    resultado.push(codigo);
    usados.add(codigo);
    depois.forEach((p) => { resultado.push(p); usados.add(p); });
  }
  return resultado;
}

function inserirComAdjacenciaParceiros(novaOrdem, codigo, parceirosPorCodigo) {
  const parceirosDiretos = parceirosPorCodigo[codigo] || [];
  const codigosRelacionados = new Set(parceirosDiretos);

  for (const parceiro of parceirosDiretos) {
    const parceirosDoParceiro = parceirosPorCodigo[parceiro] || [];
    parceirosDoParceiro.forEach((p) => codigosRelacionados.add(p));
  }

  let maiorIndice = -1;
  for (const relacionado of codigosRelacionados) {
    const indice = novaOrdem.indexOf(relacionado);
    if (indice > maiorIndice) maiorIndice = indice;
  }

  if (maiorIndice !== -1) {
    novaOrdem.splice(maiorIndice + 1, 0, codigo);
  } else {
    novaOrdem.push(codigo);
  }
}

// =====================================================================
// PASSO 2: CALCULAR A POSIÇÃO (x, y) DE CADA INDIVÍDUO
// =====================================================================
function calcularPosicoes(individuos, relacionamentos) {
  const porCodigo = {};
  individuos.forEach((ind) => { porCodigo[ind.codigo] = ind; });

  const porGeracao = {};
  individuos.forEach((ind) => {
    if (!porGeracao[ind.geracao]) porGeracao[ind.geracao] = [];
    porGeracao[ind.geracao].push(ind);
  });

  const geracoesExistentes = Object.keys(porGeracao).map(Number).sort((a, b) => a - b);
  const linhaPorGeracao = {};
  geracoesExistentes.forEach((geracao, indice) => { linhaPorGeracao[geracao] = indice; });

  const parceirosPorCodigo = construirParceirosPorCodigo(relacionamentos);

  const paisPorFilho = {};
  relacionamentos
    .filter((r) => r.tipo === "filiacao")
    .forEach((f) => {
      if (!paisPorFilho[f.destino_codigo]) paisPorFilho[f.destino_codigo] = [];
      paisPorFilho[f.destino_codigo].push(f.origem_codigo);
    });

  const filhosPorChavePais = {};
  Object.entries(paisPorFilho).forEach(([filho, pais]) => {
    const chave = [...pais].sort().join("+");
    if (!filhosPorChavePais[chave]) filhosPorChavePais[chave] = [];
    filhosPorChavePais[chave].push(filho);
  });
  Object.values(filhosPorChavePais).forEach((lista) => {
    lista.sort((a, b) => porCodigo[a].posicao - porCodigo[b].posicao);
  });

  const ordemPorGeracao = {};

  const primeiraGeracao = geracoesExistentes[0];
  let ordemInicial = [...porGeracao[primeiraGeracao]]
    .sort((a, b) => a.posicao - b.posicao)
    .map((ind) => ind.codigo);
  ordemPorGeracao[primeiraGeracao] = ajustarAdjacenciaConjuges(
    ordemInicial, parceirosPorCodigo, porCodigo, primeiraGeracao
  );

  for (let i = 1; i < geracoesExistentes.length; i++) {
    const geracao = geracoesExistentes[i];
    const geracaoAnterior = geracoesExistentes[i - 1];
    const ordemAnterior = ordemPorGeracao[geracaoAnterior];

    const novaOrdem = [];
    const adicionados = new Set();
    const processados = new Set();

    for (const codigo of ordemAnterior) {
      if (processados.has(codigo)) continue;
      processados.add(codigo);

      const parceiros = parceirosPorCodigo[codigo] || [];
      const parceirosMesmaGeracao = parceiros.filter(
        (p) => porCodigo[p] && porCodigo[p].geracao === porCodigo[codigo].geracao
      );

      for (const parceiro of parceirosMesmaGeracao) {
        processados.add(parceiro);
        const chave = [codigo, parceiro].sort().join("+");
        const filhos = filhosPorChavePais[chave] || [];
        for (const filho of filhos) {
          if (!adicionados.has(filho) && porCodigo[filho] && porCodigo[filho].geracao === geracao) {
            novaOrdem.push(filho);
            adicionados.add(filho);
          }
        }
      }
    }

    const restantes = (porGeracao[geracao] || [])
      .map((ind) => ind.codigo)
      .filter((codigo) => !adicionados.has(codigo))
      .sort((a, b) => porCodigo[a].posicao - porCodigo[b].posicao);

    for (const codigo of restantes) {
      inserirComAdjacenciaParceiros(novaOrdem, codigo, parceirosPorCodigo);
      adicionados.add(codigo);
    }

    ordemPorGeracao[geracao] = ajustarAdjacenciaConjuges(novaOrdem, parceirosPorCodigo, porCodigo, geracao);
  }

  const posicoes = {};
  geracoesExistentes.forEach((geracao) => {
    const linha = linhaPorGeracao[geracao];
    ordemPorGeracao[geracao].forEach((codigo, indice) => {
      posicoes[codigo] = {
        x: MARGIN_X + indice * COL_WIDTH,
        y: MARGIN_Y + linha * ROW_HEIGHT,
      };
    });
  });

  return posicoes;
}

function calcularCodigosComLinhaDescendoDireto(relacionamentos) {
  const paisPorFilho = {};
  relacionamentos
    .filter((r) => r.tipo === "filiacao")
    .forEach((f) => {
      if (!paisPorFilho[f.destino_codigo]) paisPorFilho[f.destino_codigo] = [];
      paisPorFilho[f.destino_codigo].push(f.origem_codigo);
    });

  const codigosComLinhaDireto = new Set();
  Object.values(paisPorFilho).forEach((paisCodigos) => {
    if (paisCodigos.length === 1) {
      codigosComLinhaDireto.add(paisCodigos[0]);
    }
  });
  return codigosComLinhaDireto;
}

// =====================================================================
// PASSO 3: DESENHAR UM INDIVÍDUO
// papel_descricao SEMPRE aparece inline (é curto, por design da IA).
// observacao (quando existir) vira uma nota de rodapé numerada [n].
// =====================================================================
function desenharIndividuo(svg, individuo, pos, temLinhaDescendoAbaixo, notas) {
  const grupo = criarElementoSVG("g", { class: "individuo" });
  const corPreenchimento = individuo.afetado ? "#333333" : "white";
  const corBorda = "#222222";

  let simbolo;

  if (individuo.sexo === "M") {
    simbolo = criarElementoSVG("rect", {
      x: pos.x - TAMANHO_SIMBOLO,
      y: pos.y - TAMANHO_SIMBOLO,
      width: TAMANHO_SIMBOLO * 2,
      height: TAMANHO_SIMBOLO * 2,
      fill: corPreenchimento,
      stroke: corBorda,
      "stroke-width": 2,
    });
  } else if (individuo.sexo === "F") {
    simbolo = criarElementoSVG("circle", {
      cx: pos.x,
      cy: pos.y,
      r: TAMANHO_SIMBOLO,
      fill: corPreenchimento,
      stroke: corBorda,
      "stroke-width": 2,
    });
  } else {
    const pontos = [
      `${pos.x},${pos.y - TAMANHO_SIMBOLO}`,
      `${pos.x + TAMANHO_SIMBOLO},${pos.y}`,
      `${pos.x},${pos.y + TAMANHO_SIMBOLO}`,
      `${pos.x - TAMANHO_SIMBOLO},${pos.y}`,
    ].join(" ");
    simbolo = criarElementoSVG("polygon", {
      points: pontos,
      fill: corPreenchimento,
      stroke: corBorda,
      "stroke-width": 2,
    });
  }
  grupo.appendChild(simbolo);

  if (individuo.portador && !individuo.afetado) {
    const ponto = criarElementoSVG("circle", {
      cx: pos.x,
      cy: pos.y,
      r: 5,
      fill: "#333333",
    });
    grupo.appendChild(ponto);
  }

  if (individuo.falecido) {
    const linha = criarElementoSVG("line", {
      x1: pos.x - TAMANHO_SIMBOLO - 6,
      y1: pos.y + TAMANHO_SIMBOLO + 6,
      x2: pos.x + TAMANHO_SIMBOLO + 6,
      y2: pos.y - TAMANHO_SIMBOLO - 6,
      stroke: "#222222",
      "stroke-width": 2,
    });
    grupo.appendChild(linha);
  }

  if (individuo.probando) {
    const seta = criarElementoSVG("path", {
      d: `M ${pos.x - TAMANHO_SIMBOLO - 30} ${pos.y + TAMANHO_SIMBOLO + 22}
          L ${pos.x - TAMANHO_SIMBOLO - 2} ${pos.y + TAMANHO_SIMBOLO - 2}
          M ${pos.x - TAMANHO_SIMBOLO - 12} ${pos.y + TAMANHO_SIMBOLO + 8}
          L ${pos.x - TAMANHO_SIMBOLO - 2} ${pos.y + TAMANHO_SIMBOLO - 2}
          L ${pos.x - TAMANHO_SIMBOLO - 16} ${pos.y + TAMANHO_SIMBOLO - 8}`,
      fill: "none",
      stroke: "#1f6f5c",
      "stroke-width": 3,
      "stroke-linecap": "round",
      "stroke-linejoin": "round",
    });
    grupo.appendChild(seta);

    const rotuloP = criarElementoSVG("text", {
      x: pos.x - TAMANHO_SIMBOLO - 38,
      y: pos.y + TAMANHO_SIMBOLO + 26,
      class: "rotulo-probando",
    });
    rotuloP.textContent = "P";
    grupo.appendChild(rotuloP);
  }

  // Se houver observação clínica adicional, registra como nota numerada
  let marcadorNota = null;
  if (individuo.observacao) {
    notas.lista.push({
      numero: notas.lista.length + 1,
      codigo: individuo.codigo,
      texto: individuo.observacao,
    });
    marcadorNota = `[${notas.lista.length}]`;
  }

  // papel_descricao + marcador de nota (se houver), sempre na mesma linha,
  // já que o papel é curto por design.
  const textoPapelComNota = [individuo.papel_descricao, marcadorNota]
    .filter(Boolean)
    .join(" ");

  if (temLinhaDescendoAbaixo) {
    const xLateral = pos.x + TAMANHO_SIMBOLO + 8;

    const rotuloCodigo = criarElementoSVG("text", {
      x: xLateral,
      y: pos.y - 2,
      class: "rotulo-individuo rotulo-codigo rotulo-lateral",
    });
    rotuloCodigo.textContent = individuo.codigo;
    grupo.appendChild(rotuloCodigo);

    if (textoPapelComNota) {
      const rotuloPapel = criarElementoSVG("text", {
        x: xLateral,
        y: pos.y - 2 + ALTURA_LINHA_TEXTO,
        class: "rotulo-individuo rotulo-papel rotulo-lateral",
      });
      rotuloPapel.textContent = textoPapelComNota;
      grupo.appendChild(rotuloPapel);
    }
  } else {
    const rotuloCodigo = criarElementoSVG("text", {
      x: pos.x,
      y: pos.y + TAMANHO_SIMBOLO + 16,
      class: "rotulo-individuo rotulo-codigo",
    });
    rotuloCodigo.textContent = individuo.codigo;
    grupo.appendChild(rotuloCodigo);

    if (textoPapelComNota) {
      const rotuloPapel = criarElementoSVG("text", {
        x: pos.x,
        y: pos.y + TAMANHO_SIMBOLO + 30,
        class: "rotulo-individuo rotulo-papel",
      });
      rotuloPapel.textContent = textoPapelComNota;
      grupo.appendChild(rotuloPapel);
    }
  }

  svg.appendChild(grupo);
}

// =====================================================================
// PASSO 4: DESENHAR AS LINHAS DE UNIÃO (casais)
// =====================================================================
function desenharUnioes(svg, relacionamentos, posicoes) {
  const unioes = relacionamentos.filter((r) => r.tipo === "uniao");

  for (const uniao of unioes) {
    const pOrigem = posicoes[uniao.origem_codigo];
    const pDestino = posicoes[uniao.destino_codigo];
    if (!pOrigem || !pDestino) continue;

    const y = pOrigem.y;
    const xEsquerda = Math.min(pOrigem.x, pDestino.x) + TAMANHO_SIMBOLO;
    const xDireita = Math.max(pOrigem.x, pDestino.x) - TAMANHO_SIMBOLO;

    if (uniao.consanguineo) {
      svg.appendChild(criarElementoSVG("line", {
        x1: xEsquerda, y1: y - 2, x2: xDireita, y2: y - 2,
        stroke: "#222222", "stroke-width": 2,
      }));
      svg.appendChild(criarElementoSVG("line", {
        x1: xEsquerda, y1: y + 2, x2: xDireita, y2: y + 2,
        stroke: "#222222", "stroke-width": 2,
      }));
    } else {
      svg.appendChild(criarElementoSVG("line", {
        x1: xEsquerda, y1: y, x2: xDireita, y2: y,
        stroke: "#222222", "stroke-width": 2,
      }));
    }
  }
}

// =====================================================================
// PASSO 5: DESENHAR AS LINHAS DE FILIAÇÃO (pais -> filhos)
// =====================================================================
function desenharFiliacoes(svg, relacionamentos, posicoes) {
  const filiacoes = relacionamentos.filter((r) => r.tipo === "filiacao");

  const paisPorFilho = {};
  for (const f of filiacoes) {
    if (!paisPorFilho[f.destino_codigo]) {
      paisPorFilho[f.destino_codigo] = [];
    }
    paisPorFilho[f.destino_codigo].push(f.origem_codigo);
  }

  const filhosPorCasal = {};
  const filhosDePaiUnico = [];

  for (const [filhoCodigo, paisCodigos] of Object.entries(paisPorFilho)) {
    if (paisCodigos.length >= 2) {
      const chave = [...paisCodigos].sort().join("+");
      if (!filhosPorCasal[chave]) filhosPorCasal[chave] = [];
      filhosPorCasal[chave].push(filhoCodigo);
    } else {
      filhosDePaiUnico.push({ pai: paisCodigos[0], filho: filhoCodigo });
    }
  }

  for (const [chaveCasal, filhosCodigos] of Object.entries(filhosPorCasal)) {
    const [codigoA, codigoB] = chaveCasal.split("+");
    const pA = posicoes[codigoA];
    const pB = posicoes[codigoB];
    if (!pA || !pB) continue;

    const xMeioCasal = (pA.x + pB.x) / 2;
    const yCasal = pA.y;
    const yLinhaIrmandade = yCasal + ROW_HEIGHT / 2;

    svg.appendChild(criarElementoSVG("line", {
      x1: xMeioCasal, y1: yCasal, x2: xMeioCasal, y2: yLinhaIrmandade,
      stroke: "#222222", "stroke-width": 2,
    }));

    const xsFilhos = filhosCodigos
      .map((codigo) => posicoes[codigo])
      .filter(Boolean)
      .map((p) => p.x);

    if (xsFilhos.length === 0) continue;

    const xMinFilhos = Math.min(...xsFilhos, xMeioCasal);
    const xMaxFilhos = Math.max(...xsFilhos, xMeioCasal);

    svg.appendChild(criarElementoSVG("line", {
      x1: xMinFilhos, y1: yLinhaIrmandade, x2: xMaxFilhos, y2: yLinhaIrmandade,
      stroke: "#222222", "stroke-width": 2,
    }));

    for (const codigoFilho of filhosCodigos) {
      const pFilho = posicoes[codigoFilho];
      if (!pFilho) continue;
      svg.appendChild(criarElementoSVG("line", {
        x1: pFilho.x, y1: yLinhaIrmandade, x2: pFilho.x, y2: pFilho.y - TAMANHO_SIMBOLO,
        stroke: "#222222", "stroke-width": 2,
      }));
    }
  }

  for (const { pai, filho } of filhosDePaiUnico) {
    const pPai = posicoes[pai];
    const pFilho = posicoes[filho];
    if (!pPai || !pFilho) continue;

    const yIntermediario = pFilho.y - TAMANHO_SIMBOLO - 20;

    svg.appendChild(criarElementoSVG("line", {
      x1: pPai.x, y1: pPai.y, x2: pPai.x, y2: yIntermediario,
      stroke: "#222222", "stroke-width": 2,
    }));
    svg.appendChild(criarElementoSVG("line", {
      x1: pPai.x, y1: yIntermediario, x2: pFilho.x, y2: yIntermediario,
      stroke: "#222222", "stroke-width": 2,
    }));
    svg.appendChild(criarElementoSVG("line", {
      x1: pFilho.x, y1: yIntermediario, x2: pFilho.x, y2: pFilho.y - TAMANHO_SIMBOLO,
      stroke: "#222222", "stroke-width": 2,
    }));
  }
}

// =====================================================================
// PASSO 6: MONTAR O SVG COMPLETO
// =====================================================================
function montarSVG(dados) {
  const posicoes = calcularPosicoes(dados.individuos, dados.relacionamentos);
  const codigosComLinhaDireto = calcularCodigosComLinhaDescendoDireto(dados.relacionamentos);
  const notas = { lista: [] };

  const todasPosicoes = Object.values(posicoes);
  const larguraMaxima = Math.max(...todasPosicoes.map((p) => p.x), 0) + MARGIN_X + 160;
  const alturaMaxima = Math.max(...todasPosicoes.map((p) => p.y), 0) + MARGIN_Y + 50;

  const svg = criarElementoSVG("svg", {
    width: larguraMaxima,
    height: alturaMaxima,
    viewBox: `0 0 ${larguraMaxima} ${alturaMaxima}`,
  });

  desenharUnioes(svg, dados.relacionamentos, posicoes);
  desenharFiliacoes(svg, dados.relacionamentos, posicoes);
  for (const individuo of dados.individuos) {
    const temLinhaDescendoAbaixo = codigosComLinhaDireto.has(individuo.codigo);
    desenharIndividuo(svg, individuo, posicoes[individuo.codigo], temLinhaDescendoAbaixo, notas);
  }

  return { svg, notas: notas.lista };
}

// =====================================================================
// Renderiza a caixa de notas de rodapé
// =====================================================================
function montarNotas(notas) {
  const container = document.getElementById("notasContainer");
  if (!container) return;

  if (notas.length === 0) {
    container.innerHTML = "";
    return;
  }

  const itens = notas
    .map((nota) => `<li><strong>[${nota.numero}] ${nota.codigo}</strong> — ${nota.texto}</li>`)
    .join("");

  container.innerHTML = `
    <h2>Notas</h2>
    <ul class="lista-notas">${itens}</ul>
  `;
}

// =====================================================================
// LEGENDA (fixa, não depende dos dados)
// =====================================================================
function montarLegenda() {
  const itens = [
    { simboloSVG: '<rect x="2" y="2" width="20" height="20" fill="white" stroke="#222" stroke-width="2"/>', texto: "Sexo masculino" },
    { simboloSVG: '<circle cx="12" cy="12" r="10" fill="white" stroke="#222" stroke-width="2"/>', texto: "Sexo feminino" },
    { simboloSVG: '<rect x="2" y="2" width="20" height="20" fill="#333"/>', texto: "Afetado" },
    { simboloSVG: '<circle cx="12" cy="12" r="10" fill="white" stroke="#222" stroke-width="2"/><circle cx="12" cy="12" r="3" fill="#333"/>', texto: "Portador" },
    { simboloSVG: '<line x1="2" y1="22" x2="22" y2="2" stroke="#222" stroke-width="2"/><rect x="2" y="2" width="20" height="20" fill="white" stroke="#222" stroke-width="2"/>', texto: "Falecido" },
  ];

  const container = document.getElementById("legendaContainer");
  container.innerHTML = "";
  for (const item of itens) {
    const div = document.createElement("div");
    div.className = "legenda-item";
    div.innerHTML = `<svg width="24" height="24">${item.simboloSVG}</svg><span>${item.texto}</span>`;
    container.appendChild(div);
  }
}

// =====================================================================
// LIGAÇÃO COM A INTERFACE (botão, mensagens de erro)
// =====================================================================
async function carregarEDesenhar() {
  const consultaId = document.getElementById("consultaId").value;
  const mensagem = document.getElementById("mensagem");
  const container = document.getElementById("heredogramaContainer");

  mensagem.textContent = "";
  container.innerHTML = "";
  const notasContainer = document.getElementById("notasContainer");
  if (notasContainer) notasContainer.innerHTML = "";
  // Desabilita a exportação enquanto carrega/troca de consulta - só faz
  // sentido exportar depois de um heredograma carregado com sucesso
  // (ver exportar-heredograma.js).
  desabilitarBotoesExportacao();

  if (!consultaId) {
    mensagem.textContent = "Informe o ID da consulta.";
    return;
  }

  try {
    mensagem.textContent = "Carregando...";
    const dados = await buscarHeredograma(consultaId);
    const { svg, notas } = montarSVG(dados);
    container.appendChild(svg);
    montarNotas(notas);
    mensagem.textContent = "";

    await prepararExportacao(consultaId, svg, notas, mensagem);
  } catch (erro) {
    mensagem.textContent = `Erro: ${erro.message}`;
  }
}

document.getElementById("btnCarregar").addEventListener("click", carregarEDesenhar);
montarLegenda();

function obterParametroURL(nome) {
  const parametros = new URLSearchParams(window.location.search);
  return parametros.get(nome);
}

const consultaIdNaURL = obterParametroURL("consulta_id");
if (consultaIdNaURL) {
  document.getElementById("consultaId").value = consultaIdNaURL;
  carregarEDesenhar();
}