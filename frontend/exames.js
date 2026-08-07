function obterParametroURL(nome) {
  const parametros = new URLSearchParams(window.location.search);
  return parametros.get(nome);
}

// Evita o efeito de "voltar um dia" que `new Date("YYYY-MM-DD")` causa em
// fusos horários atrás de UTC - formata direto a partir da string ISO.
function formatarData(dataISO) {
  if (!dataISO) return "-";
  const [ano, mes, dia] = dataISO.split("-");
  return `${dia}/${mes}/${ano}`;
}

const consultaId = obterParametroURL("consulta_id");
let nomePorIndividuoId = {};

const LABEL_STATUS = {
  solicitado: "Solicitado",
  em_andamento: "Em andamento",
  concluido: "Concluído",
  cancelado: "Cancelado",
};

// =====================================================================
// Carrega o título da consulta
// =====================================================================
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
// Carrega os indivíduos do heredograma para o <select>
// =====================================================================
async function carregarIndividuos() {
  const select = document.getElementById("individuo");
  const mensagem = document.getElementById("mensagemHeredograma");

  const resposta = await fetch(`/consultas/${consultaId}/heredograma`);
  if (!resposta.ok) {
    select.disabled = true;
    mensagem.textContent = "Heredograma ainda não foi gerado para esta consulta.";
    return;
  }

  const heredograma = await resposta.json();
  for (const individuo of heredograma.individuos) {
    const rotulo = individuo.papel_descricao
      ? `${individuo.codigo} - ${individuo.papel_descricao}`
      : individuo.codigo;
    nomePorIndividuoId[individuo.id] = rotulo;

    const opcao = document.createElement("option");
    opcao.value = individuo.id;
    opcao.textContent = rotulo;
    select.appendChild(opcao);
  }
}

// =====================================================================
// Carrega e renderiza a lista de exames
// =====================================================================
async function carregarExames() {
  const corpo = document.getElementById("corpoTabelaExames");
  corpo.innerHTML = "<tr><td colspan='6'>Carregando...</td></tr>";

  const resposta = await fetch(`/consultas/${consultaId}/exames`);
  const exames = await resposta.json();

  if (exames.length === 0) {
    corpo.innerHTML = "<tr><td colspan='6'>Nenhum exame registrado ainda.</td></tr>";
    return;
  }

  corpo.innerHTML = "";
  for (const exame of exames) {
    const nomeIndividuo = exame.individuo_id
      ? (nomePorIndividuoId[exame.individuo_id] || "-")
      : "Paciente/consulta geral";

    const linha = document.createElement("tr");
    linha.id = `linha-exame-${exame.id}`;
    linha.innerHTML = `
      <td>${exame.tipo_exame}</td>
      <td>${nomeIndividuo}</td>
      <td>
        <select data-exame-id="${exame.id}" class="select-status">
          <option value="solicitado" ${exame.status === "solicitado" ? "selected" : ""}>${LABEL_STATUS.solicitado}</option>
          <option value="em_andamento" ${exame.status === "em_andamento" ? "selected" : ""}>${LABEL_STATUS.em_andamento}</option>
          <option value="concluido" ${exame.status === "concluido" ? "selected" : ""}>${LABEL_STATUS.concluido}</option>
          <option value="cancelado" ${exame.status === "cancelado" ? "selected" : ""}>${LABEL_STATUS.cancelado}</option>
        </select>
      </td>
      <td>${formatarData(exame.data_solicitacao)}</td>
      <td>${formatarData(exame.data_resultado)}</td>
      <td>
        <a href="#" class="link-acao" data-toggle-anexos="${exame.id}">Anexos</a>
        <button type="button" class="botao-secundario" data-remover-id="${exame.id}">Remover</button>
      </td>
    `;
    corpo.appendChild(linha);
  }

  corpo.querySelectorAll(".select-status").forEach((select) => {
    select.addEventListener("change", () => {
      atualizarStatus(select.dataset.exameId, select.value);
    });
  });

  corpo.querySelectorAll("[data-remover-id]").forEach((botao) => {
    botao.addEventListener("click", () => {
      removerExame(botao.dataset.removerId);
    });
  });

  corpo.querySelectorAll("[data-toggle-anexos]").forEach((link) => {
    link.addEventListener("click", (evento) => {
      evento.preventDefault();
      alternarPainelAnexos(link.dataset.toggleAnexos);
    });
  });
}

// =====================================================================
// Painel de anexos de um exame específico - expande/recolhe uma linha
// logo abaixo da linha do exame na tabela, com o formulário de upload
// e a lista de documentos já anexados (ver anexos.js).
// =====================================================================
function alternarPainelAnexos(exameId) {
  const linhaExistente = document.getElementById(`linha-anexos-${exameId}`);
  if (linhaExistente) {
    linhaExistente.remove();
    return;
  }

  const linhaExame = document.getElementById(`linha-exame-${exameId}`);
  if (!linhaExame) return;

  const linhaAnexos = document.createElement("tr");
  linhaAnexos.id = `linha-anexos-${exameId}`;
  linhaAnexos.innerHTML = `
    <td colspan="6">
      <div class="painel-anexos">
        <form id="formAnexoExame${exameId}">
          <div class="campo campo-largo">
            <label for="arquivoAnexoExame${exameId}">Selecionar arquivo (PDF, JPEG ou PNG, até 10MB)</label>
            <input type="file" id="arquivoAnexoExame${exameId}" accept=".pdf,.jpg,.jpeg,.png" required>
          </div>
          <button type="submit" class="botao-secundario">Enviar</button>
          <span id="mensagemAnexoExame${exameId}"></span>
        </form>
        <div id="listaAnexosExame${exameId}"></div>
      </div>
    </td>
  `;
  linhaExame.insertAdjacentElement("afterend", linhaAnexos);

  inicializarAnexos({
    baseUrl: `/exames/${exameId}`,
    formId: `formAnexoExame${exameId}`,
    inputId: `arquivoAnexoExame${exameId}`,
    mensagemId: `mensagemAnexoExame${exameId}`,
    listaId: `listaAnexosExame${exameId}`,
  });
}

// =====================================================================
// Registra um novo exame
// =====================================================================
document.getElementById("formExame").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const mensagem = document.getElementById("mensagemExame");
  mensagem.textContent = "";

  const corpo = {
    individuo_id: document.getElementById("individuo").value
      ? Number(document.getElementById("individuo").value)
      : null,
    tipo_exame: document.getElementById("tipoExame").value,
    data_solicitacao: document.getElementById("dataSolicitacao").value || null,
    resultado: document.getElementById("resultado").value || null,
    observacoes: document.getElementById("observacoes").value || null,
  };

  try {
    const resposta = await fetchAutenticado(`/consultas/${consultaId}/exames`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    });

    if (!resposta.ok) {
      const erro = await resposta.json();
      throw new Error(erro.detail || "Erro ao registrar exame.");
    }

    document.getElementById("formExame").reset();
    mensagem.textContent = "Exame registrado com sucesso!";
    mensagem.className = "sucesso";
    carregarExames();
  } catch (erro) {
    mensagem.textContent = erro.message;
    mensagem.className = "erro";
  }
});

// =====================================================================
// Atualiza o status de um exame
// =====================================================================
async function atualizarStatus(exameId, novoStatus) {
  try {
    const resposta = await fetchAutenticado(
      `/consultas/${consultaId}/exames/${exameId}`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: novoStatus }),
      }
    );

    if (!resposta.ok) {
      const erro = await resposta.json();
      alert(erro.detail || "Erro ao atualizar status.");
      carregarExames();
    }
  } catch (erro) {
    alert(erro.message);
  }
}

// =====================================================================
// Remove um exame
// =====================================================================
async function removerExame(exameId) {
  const confirmou = confirm("Remover este exame?");
  if (!confirmou) return;

  try {
    const resposta = await fetchAutenticado(
      `/consultas/${consultaId}/exames/${exameId}`,
      { method: "DELETE" }
    );

    if (!resposta.ok) {
      const erro = await resposta.json().catch(() => ({}));
      throw new Error(erro.detail || "Erro ao remover.");
    }

    carregarExames();
  } catch (erro) {
    alert(erro.message);
  }
}

// =====================================================================
// Inicialização
// =====================================================================
if (!consultaId) {
  document.getElementById("tituloConsulta").textContent = "Nenhuma consulta selecionada.";
} else {
  carregarTituloConsulta();
  carregarIndividuos().then(carregarExames);
}
