function obterParametroURL(nome) {
  const parametros = new URLSearchParams(window.location.search);
  return parametros.get(nome);
}

const consultaId = obterParametroURL("consulta_id");
let nomePorEspecialidadeId = {};

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
// Carrega as especialidades para o <select>
// =====================================================================
async function carregarEspecialidades() {
  const resposta = await fetch("/especialidades/");
  const especialidades = await resposta.json();

  const select = document.getElementById("especialidade");
  for (const especialidade of especialidades) {
    nomePorEspecialidadeId[especialidade.id] = especialidade.nome;
    const opcao = document.createElement("option");
    opcao.value = especialidade.id;
    opcao.textContent = especialidade.nome;
    select.appendChild(opcao);
  }
}

// =====================================================================
// Carrega e renderiza a lista de encaminhamentos
// =====================================================================
async function carregarEncaminhamentos() {
  const corpo = document.getElementById("corpoTabelaEncaminhamentos");
  corpo.innerHTML = "<tr><td colspan='5'>Carregando...</td></tr>";

  const resposta = await fetch(`/consultas/${consultaId}/encaminhamentos`);
  const encaminhamentos = await resposta.json();

  if (encaminhamentos.length === 0) {
    corpo.innerHTML = "<tr><td colspan='5'>Nenhum encaminhamento registrado ainda.</td></tr>";
    return;
  }

  corpo.innerHTML = "";
  for (const encaminhamento of encaminhamentos) {
    const nomeEspecialidade = encaminhamento.especialidade_id
      ? (nomePorEspecialidadeId[encaminhamento.especialidade_id] || "-")
      : "Não especificada";
    const dataFormatada = new Date(encaminhamento.criado_em).toLocaleDateString("pt-BR");

    const linha = document.createElement("tr");
    linha.innerHTML = `
      <td>${dataFormatada}</td>
      <td>${nomeEspecialidade}</td>
      <td>${encaminhamento.motivo}</td>
      <td>
        <select data-encaminhamento-id="${encaminhamento.id}" class="select-status">
          <option value="pendente" ${encaminhamento.status === "pendente" ? "selected" : ""}>Pendente</option>
          <option value="concluido" ${encaminhamento.status === "concluido" ? "selected" : ""}>Concluído</option>
          <option value="cancelado" ${encaminhamento.status === "cancelado" ? "selected" : ""}>Cancelado</option>
        </select>
      </td>
      <td>
        <button type="button" class="botao-secundario" data-remover-id="${encaminhamento.id}">Remover</button>
      </td>
    `;
    corpo.appendChild(linha);
  }

  corpo.querySelectorAll(".select-status").forEach((select) => {
    select.addEventListener("change", () => {
      atualizarStatus(select.dataset.encaminhamentoId, select.value);
    });
  });

  corpo.querySelectorAll("[data-remover-id]").forEach((botao) => {
    botao.addEventListener("click", () => {
      removerEncaminhamento(botao.dataset.removerId);
    });
  });
}

// =====================================================================
// Registra um novo encaminhamento
// =====================================================================
document.getElementById("formEncaminhamento").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const mensagem = document.getElementById("mensagemEncaminhamento");
  mensagem.textContent = "";

  const corpo = {
    especialidade_id: document.getElementById("especialidade").value
      ? Number(document.getElementById("especialidade").value)
      : null,
    motivo: document.getElementById("motivo").value,
  };

  try {
    const resposta = await fetchAutenticado(`/consultas/${consultaId}/encaminhamentos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    });

    if (!resposta.ok) {
      const erro = await resposta.json();
      throw new Error(erro.detail || "Erro ao registrar encaminhamento.");
    }

    document.getElementById("formEncaminhamento").reset();
    mensagem.textContent = "Encaminhamento registrado com sucesso!";
    mensagem.className = "sucesso";
    carregarEncaminhamentos();
  } catch (erro) {
    mensagem.textContent = erro.message;
    mensagem.className = "erro";
  }
});

// =====================================================================
// Atualiza o status de um encaminhamento
// =====================================================================
async function atualizarStatus(encaminhamentoId, novoStatus) {
  try {
    const resposta = await fetchAutenticado(
      `/consultas/${consultaId}/encaminhamentos/${encaminhamentoId}`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: novoStatus }),
      }
    );

    if (!resposta.ok) {
      const erro = await resposta.json();
      alert(erro.detail || "Erro ao atualizar status.");
      carregarEncaminhamentos();
    }
  } catch (erro) {
    alert(erro.message);
  }
}

// =====================================================================
// Remove um encaminhamento
// =====================================================================
async function removerEncaminhamento(encaminhamentoId) {
  const confirmou = confirm("Remover este encaminhamento?");
  if (!confirmou) return;

  try {
    const resposta = await fetchAutenticado(
      `/consultas/${consultaId}/encaminhamentos/${encaminhamentoId}`,
      { method: "DELETE" }
    );

    if (!resposta.ok) {
      const erro = await resposta.json().catch(() => ({}));
      throw new Error(erro.detail || "Erro ao remover.");
    }

    carregarEncaminhamentos();
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
  carregarEspecialidades().then(carregarEncaminhamentos);
}