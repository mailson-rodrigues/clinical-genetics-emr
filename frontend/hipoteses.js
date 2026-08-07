function obterParametroURL(nome) {
  const parametros = new URLSearchParams(window.location.search);
  return parametros.get(nome);
}

const consultaId = obterParametroURL("consulta_id");

async function carregarTituloConsulta() {
  const resposta = await fetch(`/consultas/${consultaId}`);
  if (!resposta.ok) {
    document.getElementById("tituloConsulta").textContent = "Consulta não encontrada.";
    return;
  }
  const consulta = await resposta.json();
  document.getElementById("tituloConsulta").textContent =
    `Consulta #${consulta.id} — ${consulta.condicao_investigada}`;
}

// =====================================================================
// Lista de fontes de uma hipótese (título + link clicável + origem) -
// função isolada porque é reaproveitada tanto na renderização inicial
// quanto para atualizar só essa lista depois de "Buscar mais fontes"
// (sem recarregar a página).
// =====================================================================
function renderizarFontes(fontes) {
  if (fontes.length === 0) {
    return '<p class="mensagem-discreta">Nenhuma fonte listada.</p>';
  }

  const itens = fontes.map((fonte) => `
    <li class="item-anexo">
      <a href="${fonte.url}" target="_blank" rel="noopener noreferrer">${fonte.titulo || fonte.url}</a>
      <span class="mensagem-discreta">${fonte.origem}</span>
    </li>
  `).join("");

  return `<ul class="lista-anexos">${itens}</ul>`;
}

function renderizarHipoteses(hipoteses) {
  const container = document.getElementById("listaHipoteses");

  if (hipoteses.length === 0) {
    container.innerHTML = "<p>Nenhuma hipótese gerada ainda.</p>";
    return;
  }

  // Mais provável primeiro - já vem ordenado da API (?consulta_id=...
  // ordena por "ordem" no backend), mas reordena aqui também para não
  // depender disso.
  const hipotesesOrdenadas = [...hipoteses].sort((a, b) => a.ordem - b.ordem);

  container.innerHTML = "";
  for (const hipotese of hipotesesOrdenadas) {
    const cidHtml = hipotese.cid_sugerido
      ? `<span class="codigo-clinico">${hipotese.cid_sugerido}</span>`
      : "";

    const cartao = document.createElement("section");
    cartao.className = "cartao";
    cartao.innerHTML = `
      <h3>${hipotese.condicao} ${cidHtml}</h3>
      <p>${hipotese.justificativa}</p>
      <div id="fontesHipotese${hipotese.id}">${renderizarFontes(hipotese.fontes)}</div>
      <button type="button" class="botao-secundario" data-mais-fontes="${hipotese.id}">Buscar mais fontes</button>
      <span id="mensagemMaisFontes${hipotese.id}" class="mensagem-discreta"></span>
    `;
    container.appendChild(cartao);
  }

  container.querySelectorAll("[data-mais-fontes]").forEach((botao) => {
    botao.addEventListener("click", () => buscarMaisFontes(botao.dataset.maisFontes));
  });
}

async function carregarHipoteses() {
  const resposta = await fetchAutenticado(`/consultas/${consultaId}/hipoteses`);
  if (!resposta.ok) {
    document.getElementById("listaHipoteses").innerHTML = '<p class="erro">Erro ao carregar hipóteses.</p>';
    return;
  }
  const hipoteses = await resposta.json();
  renderizarHipoteses(hipoteses);
}

document.getElementById("btnGerarHipoteses").addEventListener("click", async () => {
  const mensagem = document.getElementById("mensagemGeracao");
  mensagem.textContent = "Gerando hipóteses (a busca na web pode levar um instante)...";
  mensagem.className = "mensagem-discreta";

  try {
    const resposta = await fetchAutenticado(`/consultas/${consultaId}/hipoteses`, {
      method: "POST",
    });

    if (!resposta.ok) {
      const erro = await resposta.json().catch(() => ({}));
      throw new Error(erro.detail || "Erro ao gerar hipóteses.");
    }

    mensagem.textContent = "Hipóteses geradas com sucesso!";
    mensagem.className = "sucesso";
    carregarHipoteses();
  } catch (erro) {
    mensagem.textContent = erro.message;
    mensagem.className = "erro";
  }
});

// =====================================================================
// "Buscar mais fontes" - chama a rota de mais-fontes e atualiza só a
// lista de fontes daquela hipótese, sem recarregar a página inteira.
// =====================================================================
async function buscarMaisFontes(hipoteseId) {
  const mensagem = document.getElementById(`mensagemMaisFontes${hipoteseId}`);
  mensagem.textContent = "Buscando mais fontes...";
  mensagem.className = "mensagem-discreta";

  try {
    const resposta = await fetchAutenticado(
      `/consultas/${consultaId}/hipoteses/${hipoteseId}/mais-fontes`,
      { method: "POST" }
    );

    if (!resposta.ok) {
      const erro = await resposta.json().catch(() => ({}));
      throw new Error(erro.detail || "Erro ao buscar mais fontes.");
    }

    const hipoteseAtualizada = await resposta.json();
    document.getElementById(`fontesHipotese${hipoteseId}`).innerHTML =
      renderizarFontes(hipoteseAtualizada.fontes);
    mensagem.textContent = "";
  } catch (erro) {
    mensagem.textContent = erro.message;
    mensagem.className = "erro";
  }
}

// =====================================================================
// Inicialização
// =====================================================================
if (!consultaId) {
  document.getElementById("tituloConsulta").textContent = "Nenhuma consulta selecionada.";
} else {
  carregarTituloConsulta();
  carregarHipoteses();
}
