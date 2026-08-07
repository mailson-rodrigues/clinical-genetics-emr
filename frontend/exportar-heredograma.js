// =====================================================================
// Exportação do heredograma exibido (PDF e PNG), gerada inteiramente
// no navegador - reaproveita o mesmo <svg> que script.js já desenha,
// sem nenhuma rota nova no backend.
//
// PDF: usa jsPDF + svg2pdf.js para inserir o SVG como conteúdo VETORIAL
// de verdade (linhas e texto nítidos em qualquer zoom, texto
// selecionável) - em vez de rasterizar o SVG como imagem.
//
// PNG: como o formato é sempre raster, aqui SIM rasterizamos o SVG -
// via XMLSerializer + Image + canvas.drawImage - e exportamos com
// canvas.toDataURL()/toBlob(). Não há alternativa vetorial para PNG.
//
// A legenda e as notas de rodapé são redesenhadas "na mão" (formas
// jsPDF / canvas 2D) em vez de reaproveitar o HTML de
// #legendaContainer/#notasContainer, porque as APIs de desenho do
// jsPDF e do Canvas2D são bem diferentes da manipulação de DOM/SVG -
// isso espelha o conteúdo fixo de montarLegenda() (5 itens) em
// script.js; se a legenda mudar lá, precisa mudar aqui também.
// =====================================================================

let dadosExportacaoAtual = null;

function desabilitarBotoesExportacao() {
  document.getElementById("btnExportarPdf").disabled = true;
  document.getElementById("btnExportarPng").disabled = true;
  dadosExportacaoAtual = null;
}

function habilitarBotoesExportacao() {
  document.getElementById("btnExportarPdf").disabled = false;
  document.getElementById("btnExportarPng").disabled = false;
}

function formatarDataHoraExtenso(data) {
  return data.toLocaleString("pt-BR");
}

function formatarDataParaNomeArquivo(data) {
  const ano = data.getFullYear();
  const mes = String(data.getMonth() + 1).padStart(2, "0");
  const dia = String(data.getDate()).padStart(2, "0");
  return `${ano}${mes}${dia}`;
}

function nomeArquivoExportacao(extensao) {
  const consultaId = dadosExportacaoAtual.consultaId;
  const dataArquivo = formatarDataParaNomeArquivo(new Date());
  return `heredograma_consulta_${consultaId}_${dataArquivo}.${extensao}`;
}

// =====================================================================
// Chamada por script.js logo depois de desenhar o heredograma com
// sucesso - busca os dados complementares (consulta, paciente) e só
// então habilita os botões de exportação.
// =====================================================================
async function prepararExportacao(consultaId, svgElement, notas, elementoMensagem) {
  try {
    const respostaConsulta = await fetch(`/consultas/${consultaId}`);
    if (!respostaConsulta.ok) {
      throw new Error("Não foi possível carregar os dados da consulta para exportação.");
    }
    const consulta = await respostaConsulta.json();

    let nomePaciente = "-";
    const respostaPaciente = await fetch(`/pacientes/${consulta.paciente_id}`);
    if (respostaPaciente.ok) {
      const paciente = await respostaPaciente.json();
      nomePaciente = paciente.nome_social || paciente.nome;
    }

    dadosExportacaoAtual = {
      consultaId: Number(consultaId),
      condicaoInvestigada: consulta.condicao_investigada,
      nomePaciente,
      svgElement,
      notas,
    };

    habilitarBotoesExportacao();
  } catch (erro) {
    if (elementoMensagem) {
      elementoMensagem.textContent = `Heredograma carregado, mas a exportação não pôde ser preparada: ${erro.message}`;
    }
  }
}

// =====================================================================
// Itens da legenda - espelha montarLegenda() em script.js
// =====================================================================
const ITENS_LEGENDA = [
  "Sexo masculino",
  "Sexo feminino",
  "Afetado",
  "Portador",
  "Falecido",
];

// =====================================================================
// Paginação do PDF: título, desenho do heredograma, legenda e notas são
// desenhados em sequência num Y que só cresce - sem checar o espaço
// restante da página, qualquer bloco que "sobrasse" (tipicamente
// legenda/notas, em heredogramas com muitas notas) ficava posicionado
// abaixo do fim da página e não aparecia no PDF. `garantirEspaco` checa
// se um bloco de altura conhecida cabe no que resta da página atual
// (respeitando uma margem inferior de segurança) e, se não couber,
// chama doc.addPage() e devolve o Y do topo da nova página - cada bloco
// (legenda inteira; cada nota individualmente, já que pode haver
// muitas) passa por essa checagem antes de ser desenhado.
//
// O desenho do heredograma em si é a única exceção de propósito: ele
// só é escalado para caber na LARGURA da página (nunca dividido entre
// páginas) - um heredograma grande o bastante para ultrapassar a altura
// de uma página sozinho continua avançando por cima da margem, mas
// isso é aceitável (não é o bug relatado, que era especificamente
// sobre legenda/notas desaparecerem).
// =====================================================================
const PONTOS_POR_MM = 2.834645669291339;
const MARGEM_INFERIOR_SEGURANCA = 20 * PONTOS_POR_MM; // ~20mm, conforme pedido
const MARGEM_SUPERIOR_NOVA_PAGINA = 40; // mesmo valor do `margem` inicial em exportarPDF()

function garantirEspaco(doc, cursorY, alturaNecessaria) {
  const alturaPagina = doc.internal.pageSize.getHeight();
  if (cursorY + alturaNecessaria > alturaPagina - MARGEM_INFERIOR_SEGURANCA) {
    doc.addPage();
    return MARGEM_SUPERIOR_NOVA_PAGINA;
  }
  return cursorY;
}

const ALTURA_TITULO_BLOCO = 18;
const ALTURA_ITEM_LEGENDA = 16;
const RESPIRO_FINAL_BLOCO = 10;
const ALTURA_TOTAL_LEGENDA =
  ALTURA_TITULO_BLOCO + ITENS_LEGENDA.length * ALTURA_ITEM_LEGENDA + RESPIRO_FINAL_BLOCO;

function desenharLegendaPDF(doc, x, yInicial) {
  // A legenda tem tamanho fixo (5 itens) - cabe checar o espaço UMA vez
  // pro bloco inteiro, em vez de item por item.
  let y = garantirEspaco(doc, yInicial, ALTURA_TOTAL_LEGENDA);

  doc.setFont(undefined, "bold");
  doc.setFontSize(13);
  doc.text("Legenda", x, y);
  doc.setFont(undefined, "normal");
  y += ALTURA_TITULO_BLOCO;

  doc.setFontSize(10);
  doc.setDrawColor(34, 34, 34);
  const cx = x + 6;

  // Sexo masculino: quadrado contornado
  doc.rect(cx - 6, y - 9, 12, 12);
  doc.text(ITENS_LEGENDA[0], x + 24, y);
  y += ALTURA_ITEM_LEGENDA;

  // Sexo feminino: círculo contornado
  doc.circle(cx, y - 3, 6);
  doc.text(ITENS_LEGENDA[1], x + 24, y);
  y += ALTURA_ITEM_LEGENDA;

  // Afetado: quadrado preenchido
  doc.setFillColor(51, 51, 51);
  doc.rect(cx - 6, y - 9, 12, 12, "F");
  doc.text(ITENS_LEGENDA[2], x + 24, y);
  y += ALTURA_ITEM_LEGENDA;

  // Portador: círculo contornado com ponto central preenchido
  doc.circle(cx, y - 3, 6);
  doc.setFillColor(51, 51, 51);
  doc.circle(cx, y - 3, 2, "F");
  doc.text(ITENS_LEGENDA[3], x + 24, y);
  y += ALTURA_ITEM_LEGENDA;

  // Falecido: quadrado contornado com linha diagonal
  doc.rect(cx - 6, y - 9, 12, 12);
  doc.line(cx - 6, y + 3, cx + 6, y - 9);
  doc.text(ITENS_LEGENDA[4], x + 24, y);
  y += ALTURA_ITEM_LEGENDA;

  return y + RESPIRO_FINAL_BLOCO;
}

const ALTURA_LINHA_NOTA = 13;
const ESPACAMENTO_ENTRE_NOTAS = 4;

// =====================================================================
// Hipóteses diagnósticas (ver hipoteses.html/.js) - se a consulta tiver
// hipóteses geradas, o PDF ganha uma seção extra com o MESMO aviso
// ético exibido na tela (mantenha os dois textos idênticos se um dia
// precisar editar) antes da lista. Se não houver hipóteses, a seção
// simplesmente não aparece no PDF (nada de bloco vazio).
// =====================================================================
const TEXTO_AVISO_ETICO_HIPOTESES = [
  "Esta é uma sugestão gerada por inteligência artificial, com base no " +
    "padrão de heredograma e no histórico clínico registrado. Ela serve " +
    "como apoio à investigação — não é um diagnóstico.",
  "A confirmação (ou exclusão) desta hipótese deve ser feita por um " +
    "profissional habilitado, devidamente registrado em seu conselho de " +
    "classe, seguindo os protocolos clínicos e a legislação vigente. " +
    "Nenhuma decisão médica, teste genético confirmatório ou conduta " +
    "terapêutica deve se basear exclusivamente nesta sugestão.",
];

const PADDING_CAIXA_AVISO = 10;
const ESPACAMENTO_ENTRE_PARAGRAFOS_AVISO = 6;

async function buscarHipotesesParaExportacao(consultaId) {
  try {
    const resposta = await fetch(`/consultas/${consultaId}/hipoteses`);
    if (!resposta.ok) return [];
    return await resposta.json();
  } catch (erro) {
    return [];
  }
}

function desenharHipotesesPDF(doc, x, yInicial, hipoteses) {
  if (!hipoteses || hipoteses.length === 0) return yInicial;

  let y = garantirEspaco(doc, yInicial, ALTURA_TITULO_BLOCO);
  doc.setFont(undefined, "bold");
  doc.setFontSize(13);
  doc.text("Hipóteses diagnósticas", x, y);
  doc.setFont(undefined, "normal");
  y += ALTURA_TITULO_BLOCO;

  const larguraCaixa = doc.internal.pageSize.getWidth() - x * 2;
  const larguraTextoAviso = larguraCaixa - PADDING_CAIXA_AVISO * 2;

  doc.setFontSize(9);
  const linhasAviso1 = doc.splitTextToSize(TEXTO_AVISO_ETICO_HIPOTESES[0], larguraTextoAviso);
  const linhasAviso2 = doc.splitTextToSize(TEXTO_AVISO_ETICO_HIPOTESES[1], larguraTextoAviso);
  const alturaCaixaAviso =
    (linhasAviso1.length + linhasAviso2.length) * ALTURA_LINHA_NOTA +
    PADDING_CAIXA_AVISO * 2 +
    ESPACAMENTO_ENTRE_PARAGRAFOS_AVISO;

  y = garantirEspaco(doc, y, alturaCaixaAviso);

  // Caixa com fundo e borda em destaque - mesma ideia visual do
  // ".aviso-etico" em style.css (não dá pra reaproveitar CSS aqui, o
  // jsPDF desenha em pontos/RGB).
  doc.setFillColor(244, 229, 229); // ~ var(--cor-perigo-claro)
  doc.setDrawColor(155, 59, 59); // ~ var(--cor-perigo)
  doc.setLineWidth(1);
  doc.rect(x, y, larguraCaixa, alturaCaixaAviso, "FD");

  let yTextoAviso = y + PADDING_CAIXA_AVISO + ALTURA_LINHA_NOTA - 4;
  doc.text(linhasAviso1, x + PADDING_CAIXA_AVISO, yTextoAviso);
  yTextoAviso += linhasAviso1.length * ALTURA_LINHA_NOTA + ESPACAMENTO_ENTRE_PARAGRAFOS_AVISO;
  doc.text(linhasAviso2, x + PADDING_CAIXA_AVISO, yTextoAviso);

  y += alturaCaixaAviso + RESPIRO_FINAL_BLOCO;

  // Lista das hipóteses (condição, CID sugerido e justificativa) -
  // cada uma checa seu próprio espaço, como as notas.
  doc.setFontSize(10);
  const larguraTextoHipotese = larguraCaixa;
  for (const hipotese of hipoteses) {
    const cabecalho = hipotese.cid_sugerido
      ? `${hipotese.condicao} (CID: ${hipotese.cid_sugerido})`
      : hipotese.condicao;
    const linhasJustificativa = doc.splitTextToSize(hipotese.justificativa, larguraTextoHipotese);
    const alturaBloco = ALTURA_LINHA_NOTA + linhasJustificativa.length * ALTURA_LINHA_NOTA + ESPACAMENTO_ENTRE_NOTAS;

    y = garantirEspaco(doc, y, alturaBloco);

    doc.setFont(undefined, "bold");
    doc.text(cabecalho, x, y);
    doc.setFont(undefined, "normal");
    y += ALTURA_LINHA_NOTA;

    doc.text(linhasJustificativa, x, y);
    y += linhasJustificativa.length * ALTURA_LINHA_NOTA + ESPACAMENTO_ENTRE_NOTAS;
  }

  return y;
}

function desenharNotasPDF(doc, x, yInicial) {
  if (dadosExportacaoAtual.notas.length === 0) return yInicial;

  let y = garantirEspaco(doc, yInicial, ALTURA_TITULO_BLOCO);
  doc.setFont(undefined, "bold");
  doc.setFontSize(13);
  doc.text("Notas", x, y);
  doc.setFont(undefined, "normal");
  y += ALTURA_TITULO_BLOCO;

  doc.setFontSize(10);
  const larguraMaxima = doc.internal.pageSize.getWidth() - x * 2;

  // Notas são desenhadas uma a uma, cada uma checando seu próprio
  // espaço (podem ser muitas, e cada uma tem altura diferente
  // dependendo de quantas linhas o texto ocupa quebrado).
  for (const nota of dadosExportacaoAtual.notas) {
    const texto = `[${nota.numero}] ${nota.codigo} — ${nota.texto}`;
    const linhas = doc.splitTextToSize(texto, larguraMaxima);
    const alturaNota = linhas.length * ALTURA_LINHA_NOTA + ESPACAMENTO_ENTRE_NOTAS;

    y = garantirEspaco(doc, y, alturaNota);
    doc.text(linhas, x, y);
    y += alturaNota;
  }

  return y;
}

// =====================================================================
// PDF (vetorial via svg2pdf.js)
// =====================================================================
async function exportarPDF() {
  if (!dadosExportacaoAtual) return;

  const mensagem = document.getElementById("mensagem");
  mensagem.textContent = "";

  try {
    const hipoteses = await buscarHipotesesParaExportacao(dadosExportacaoAtual.consultaId);

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ orientation: "landscape", unit: "pt", format: "a4" });

    const margem = 40;
    let cursorY = 40;

    doc.setFontSize(16);
    doc.setFont(undefined, "bold");
    doc.text(`Heredograma - Consulta #${dadosExportacaoAtual.consultaId}`, margem, cursorY);
    doc.setFont(undefined, "normal");
    cursorY += 22;

    doc.setFontSize(11);
    doc.text(`Condição investigada: ${dadosExportacaoAtual.condicaoInvestigada}`, margem, cursorY);
    cursorY += 16;
    doc.text(`Paciente: ${dadosExportacaoAtual.nomePaciente}`, margem, cursorY);
    cursorY += 16;
    doc.text(`Exportado em: ${formatarDataHoraExtenso(new Date())}`, margem, cursorY);
    cursorY += 24;

    const svgElement = dadosExportacaoAtual.svgElement;
    const larguraSvg = Number(svgElement.getAttribute("width"));
    const alturaSvg = Number(svgElement.getAttribute("height"));

    // CORREÇÃO DE REGRESSÃO (a versão anterior desta correção ainda
    // deixava o desenho ser cortado pela borda física da página em
    // heredogramas com várias gerações - confirmado visualmente
    // renderizando o PDF gerado). doc.svg() desenha o SVG inteiro numa
    // única página; se ele não couber no espaço disponível, o conteúdo
    // que sobra é CORTADO pela borda da página (MediaBox do PDF), não
    // continua sozinho na próxima. A garantia exigida é que TODOS os
    // indivíduos sempre apareçam completos, então:
    //   1. Escala pela LARGURA da página normalmente.
    //   2. Se, com essa escala, a altura não couber no que resta da
    //      página atual, começa uma página nova (que tem mais espaço
    //      vertical disponível, por não ter o bloco de título).
    //   3. Se mesmo assim não couber numa página inteira do zero,
    //      SÓ ENTÃO reduz a escala também pela altura - o desenho fica
    //      menor/mais denso nesse caso extremo, mas nunca cortado.
    const larguraDisponivel = doc.internal.pageSize.getWidth() - margem * 2;
    const escalaLargura = Math.min(1, larguraDisponivel / larguraSvg);

    const alturaPagina = doc.internal.pageSize.getHeight();
    const alturaDisponivelAqui = alturaPagina - cursorY - MARGEM_INFERIOR_SEGURANCA;
    const alturaDisponivelPaginaCheia = alturaPagina - MARGEM_SUPERIOR_NOVA_PAGINA - MARGEM_INFERIOR_SEGURANCA;

    let escala = escalaLargura;

    if (alturaSvg * escalaLargura > alturaDisponivelAqui) {
      doc.addPage();
      cursorY = MARGEM_SUPERIOR_NOVA_PAGINA;

      if (alturaSvg * escalaLargura > alturaDisponivelPaginaCheia) {
        escala = Math.min(escalaLargura, alturaDisponivelPaginaCheia / alturaSvg);
      }
    }

    const alturaEscalada = alturaSvg * escala;

    await doc.svg(svgElement, {
      x: margem,
      y: cursorY,
      width: larguraSvg * escala,
      height: alturaEscalada,
    });
    cursorY += alturaEscalada + 20;

    cursorY = desenharLegendaPDF(doc, margem, cursorY);
    cursorY = desenharNotasPDF(doc, margem, cursorY);
    desenharHipotesesPDF(doc, margem, cursorY, hipoteses);

    doc.save(nomeArquivoExportacao("pdf"));
  } catch (erro) {
    mensagem.textContent = `Erro ao exportar PDF: ${erro.message}`;
  }
}

// =====================================================================
// PNG (raster - SVG desenhado num <canvas> e exportado com toBlob)
// =====================================================================
function quebrarTextoCanvas(contexto, texto, larguraMaxima) {
  const palavras = texto.split(" ");
  const linhas = [];
  let linhaAtual = "";

  for (const palavra of palavras) {
    const tentativa = linhaAtual ? `${linhaAtual} ${palavra}` : palavra;
    if (linhaAtual && contexto.measureText(tentativa).width > larguraMaxima) {
      linhas.push(linhaAtual);
      linhaAtual = palavra;
    } else {
      linhaAtual = tentativa;
    }
  }
  if (linhaAtual) linhas.push(linhaAtual);
  return linhas;
}

function desenharLegendaCanvas(contexto, x, yInicial) {
  let y = yInicial;
  contexto.fillStyle = "#000000";
  contexto.font = "bold 14px sans-serif";
  contexto.fillText("Legenda", x, y);
  y += 20;

  contexto.strokeStyle = "#222222";
  contexto.lineWidth = 1.5;
  contexto.font = "12px sans-serif";
  const cx = x + 6;

  // Sexo masculino
  contexto.strokeRect(cx - 6, y - 12, 12, 12);
  contexto.fillText(ITENS_LEGENDA[0], x + 24, y - 2);
  y += 20;

  // Sexo feminino
  contexto.beginPath();
  contexto.arc(cx, y - 6, 6, 0, Math.PI * 2);
  contexto.stroke();
  contexto.fillText(ITENS_LEGENDA[1], x + 24, y - 2);
  y += 20;

  // Afetado
  contexto.fillStyle = "#333333";
  contexto.fillRect(cx - 6, y - 12, 12, 12);
  contexto.fillStyle = "#000000";
  contexto.fillText(ITENS_LEGENDA[2], x + 24, y - 2);
  y += 20;

  // Portador
  contexto.beginPath();
  contexto.arc(cx, y - 6, 6, 0, Math.PI * 2);
  contexto.stroke();
  contexto.fillStyle = "#333333";
  contexto.beginPath();
  contexto.arc(cx, y - 6, 2, 0, Math.PI * 2);
  contexto.fill();
  contexto.fillStyle = "#000000";
  contexto.fillText(ITENS_LEGENDA[3], x + 24, y - 2);
  y += 20;

  // Falecido
  contexto.strokeRect(cx - 6, y - 12, 12, 12);
  contexto.beginPath();
  contexto.moveTo(cx - 6, y);
  contexto.lineTo(cx + 6, y - 12);
  contexto.stroke();
  contexto.fillText(ITENS_LEGENDA[4], x + 24, y - 2);
  y += 20;

  return y + 10;
}

function medirAlturaNotasCanvas(contexto, larguraMaxima) {
  if (dadosExportacaoAtual.notas.length === 0) return 0;

  contexto.font = "12px sans-serif";
  let totalLinhas = 0;
  for (const nota of dadosExportacaoAtual.notas) {
    const texto = `[${nota.numero}] ${nota.codigo} — ${nota.texto}`;
    totalLinhas += quebrarTextoCanvas(contexto, texto, larguraMaxima).length;
  }
  return 24 + totalLinhas * 16;
}

function desenharNotasCanvas(contexto, x, yInicial, larguraMaxima) {
  if (dadosExportacaoAtual.notas.length === 0) return;

  let y = yInicial;
  contexto.fillStyle = "#000000";
  contexto.font = "bold 14px sans-serif";
  contexto.fillText("Notas", x, y);
  y += 20;

  contexto.font = "12px sans-serif";
  for (const nota of dadosExportacaoAtual.notas) {
    const texto = `[${nota.numero}] ${nota.codigo} — ${nota.texto}`;
    for (const linha of quebrarTextoCanvas(contexto, texto, larguraMaxima)) {
      contexto.fillText(linha, x, y);
      y += 16;
    }
  }
}

function carregarImagemSVG(svgElement) {
  const serializador = new XMLSerializer();
  const svgTexto = serializador.serializeToString(svgElement);
  const blob = new Blob([svgTexto], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  return new Promise((resolve, reject) => {
    const imagem = new Image();
    imagem.onload = () => {
      URL.revokeObjectURL(url);
      resolve(imagem);
    };
    imagem.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Falha ao rasterizar o SVG do heredograma."));
    };
    imagem.src = url;
  });
}

async function exportarPNG() {
  if (!dadosExportacaoAtual) return;

  const mensagem = document.getElementById("mensagem");
  mensagem.textContent = "";

  try {
    const svgElement = dadosExportacaoAtual.svgElement;
    const larguraSvg = Number(svgElement.getAttribute("width"));
    const alturaSvg = Number(svgElement.getAttribute("height"));

    const margem = 20;
    const alturaCabecalho = 90;
    const alturaLegenda = 20 + ITENS_LEGENDA.length * 20 + 10;
    const larguraCanvas = Math.max(larguraSvg, 520) + margem * 2;

    const canvasMedida = document.createElement("canvas");
    const alturaNotas = medirAlturaNotasCanvas(canvasMedida.getContext("2d"), larguraCanvas - margem * 2);

    const canvas = document.createElement("canvas");
    canvas.width = larguraCanvas;
    canvas.height = alturaCabecalho + alturaSvg + alturaLegenda + alturaNotas + margem * 2;
    const contexto = canvas.getContext("2d");

    contexto.fillStyle = "#ffffff";
    contexto.fillRect(0, 0, canvas.width, canvas.height);

    contexto.fillStyle = "#000000";
    contexto.font = "bold 18px sans-serif";
    contexto.fillText(`Heredograma - Consulta #${dadosExportacaoAtual.consultaId}`, margem, 30);

    contexto.font = "13px sans-serif";
    contexto.fillText(`Condição investigada: ${dadosExportacaoAtual.condicaoInvestigada}`, margem, 50);
    contexto.fillText(`Paciente: ${dadosExportacaoAtual.nomePaciente}`, margem, 68);
    contexto.fillText(`Exportado em: ${formatarDataHoraExtenso(new Date())}`, margem, 86);

    const imagemSvg = await carregarImagemSVG(svgElement);
    contexto.drawImage(imagemSvg, margem, alturaCabecalho, larguraSvg, alturaSvg);

    let y = alturaCabecalho + alturaSvg + 24;
    y = desenharLegendaCanvas(contexto, margem, y);
    desenharNotasCanvas(contexto, margem, y, larguraCanvas - margem * 2);

    canvas.toBlob((blob) => {
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = nomeArquivoExportacao("png");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }, "image/png");
  } catch (erro) {
    mensagem.textContent = `Erro ao exportar imagem: ${erro.message}`;
  }
}

document.getElementById("btnExportarPdf").addEventListener("click", exportarPDF);
document.getElementById("btnExportarPng").addEventListener("click", exportarPNG);
