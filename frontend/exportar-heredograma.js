// =====================================================================
// Export of the displayed pedigree (PDF and PNG), generated entirely
// in the browser - reuses the same <svg> that script.js already draws,
// without any new backend route.
//
// PDF: uses jsPDF + svg2pdf.js to insert the SVG as real VECTOR
// content (sharp lines and text at any zoom, selectable
// text) - instead of rasterizing the SVG as an image.
//
// PNG: since the format is always raster, here we DO rasterize the SVG -
// via XMLSerializer + Image + canvas.drawImage - and export with
// canvas.toDataURL()/toBlob(). There is no vector alternative for PNG.
//
// The legend and the footnotes are redrawn "by hand" (jsPDF /
// canvas 2D shapes) instead of reusing the HTML of
// #legendaContainer/#notasContainer, because the drawing APIs of
// jsPDF and Canvas2D are quite different from DOM/SVG manipulation -
// this mirrors the fixed content of montarLegenda() (5 items) in
// script.js; if the legend changes there, it must change here too.
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
// Called by script.js right after drawing the pedigree
// successfully - fetches the complementary data (consultation, patient) and only
// then enables the export buttons.
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
// PDF pagination: title, pedigree drawing, legend and notes are
// drawn in sequence at a Y that only grows - without checking the remaining
// space on the page, any block that "overflowed" (typically
// legend/notes, in pedigrees with many notes) was positioned
// below the end of the page and did not appear in the PDF. `garantirEspaco` checks
// whether a block of known height fits in what remains of the current page
// (respecting a safety bottom margin) and, if it does not fit,
// calls doc.addPage() and returns the Y of the top of the new page - each block
// (the whole legend; each note individually, since there may be
// many) goes through this check before being drawn.
//
// The pedigree drawing itself is the one deliberate exception: it
// is only scaled to fit the page WIDTH (never split across
// pages) - a pedigree large enough to exceed the height
// of a page on its own keeps advancing over the margin, but
// that is acceptable (it is not the reported bug, which was specifically
// about the legend/notes disappearing).
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
  // The legend has a fixed size (5 items) - it is enough to check the space ONCE
  // for the whole block, instead of item by item.
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

  // Female sex: outlined circle
  doc.circle(cx, y - 3, 6);
  doc.text(ITENS_LEGENDA[1], x + 24, y);
  y += ALTURA_ITEM_LEGENDA;

  // Afetado: quadrado preenchido
  doc.setFillColor(51, 51, 51);
  doc.rect(cx - 6, y - 9, 12, 12, "F");
  doc.text(ITENS_LEGENDA[2], x + 24, y);
  y += ALTURA_ITEM_LEGENDA;

  // Carrier: outlined circle with a filled central dot
  doc.circle(cx, y - 3, 6);
  doc.setFillColor(51, 51, 51);
  doc.circle(cx, y - 3, 2, "F");
  doc.text(ITENS_LEGENDA[3], x + 24, y);
  y += ALTURA_ITEM_LEGENDA;

  // Deceased: outlined square with a diagonal line
  doc.rect(cx - 6, y - 9, 12, 12);
  doc.line(cx - 6, y + 3, cx + 6, y - 9);
  doc.text(ITENS_LEGENDA[4], x + 24, y);
  y += ALTURA_ITEM_LEGENDA;

  return y + RESPIRO_FINAL_BLOCO;
}

const ALTURA_LINHA_NOTA = 13;
const ESPACAMENTO_ENTRE_NOTAS = 4;

// =====================================================================
// Diagnostic hypotheses (see hipoteses.html/.js) - if the consultation has
// generated hypotheses, the PDF gets an extra section with the SAME ethical
// notice shown on screen (keep both texts identical if you ever
// need to edit them) before the list. If there are no hypotheses, the section
// simply does not appear in the PDF (no empty block).
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

  // Box with a highlighted background and border - same visual idea as
  // ".aviso-etico" in style.css (CSS cannot be reused here, jsPDF
  // draws in points/RGB).
  doc.setFillColor(244, 229, 229); // ~ var(--cor-perigo-claro)
  doc.setDrawColor(155, 59, 59); // ~ var(--cor-perigo)
  doc.setLineWidth(1);
  doc.rect(x, y, larguraCaixa, alturaCaixaAviso, "FD");

  let yTextoAviso = y + PADDING_CAIXA_AVISO + ALTURA_LINHA_NOTA - 4;
  doc.text(linhasAviso1, x + PADDING_CAIXA_AVISO, yTextoAviso);
  yTextoAviso += linhasAviso1.length * ALTURA_LINHA_NOTA + ESPACAMENTO_ENTRE_PARAGRAFOS_AVISO;
  doc.text(linhasAviso2, x + PADDING_CAIXA_AVISO, yTextoAviso);

  y += alturaCaixaAviso + RESPIRO_FINAL_BLOCO;

  // List of hypotheses (condition, suggested CID and justification) -
  // each one checks its own space, like the notes.
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

  // Notes are drawn one by one, each checking its own
  // space (there may be many, and each has a different height
  // depending on how many lines the wrapped text takes).
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

    // REGRESSION FIX (the previous version of this fix still
    // let the drawing be cut off by the physical edge of the page in
    // pedigrees with several generations - confirmed visually by
    // rendering the generated PDF). doc.svg() draws the whole SVG on a
    // single page; if it does not fit in the available space, the content
    // that overflows is CUT by the page edge (PDF MediaBox), it does not
    // continue on its own on the next one. The required guarantee is that ALL
    // individuals always appear complete, so:
    //   1. Scale by the page WIDTH as usual.
    //   2. If, with that scale, the height does not fit in what remains of the
    //      current page, start a new page (which has more vertical
    //      space available, since it has no title block).
    //   3. If it still does not fit on a whole page from scratch,
    //      ONLY THEN also reduce the scale by height - the drawing gets
    //      smaller/denser in that extreme case, but never cut off.
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
// PNG (raster - SVG drawn on a <canvas> and exported with toBlob)
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
