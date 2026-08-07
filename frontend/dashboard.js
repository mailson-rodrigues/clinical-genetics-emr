function formatarDataHora(iso) {
  return new Date(iso).toLocaleString("pt-BR");
}

// =====================================================================
// Renderiza a lista de "Atividade recente" (últimas consultas) - se
// vazia (sistema novo, sem nenhuma consulta ainda), mostra uma
// chamada para ação em vez de uma lista vazia estranha.
// =====================================================================
function renderizarAtividadeRecente(itens) {
  const container = document.getElementById("listaAtividadeRecente");

  if (itens.length === 0) {
    container.innerHTML =
      '<p>Nenhuma consulta registrada ainda. ' +
      '<a href="pacientes-cadastrar.html" class="link-acao">Comece cadastrando um paciente</a>.</p>';
    return;
  }

  container.innerHTML = "";
  for (const item of itens) {
    const linha = document.createElement("div");
    linha.className = "item-atividade";
    linha.innerHTML = `
      <div>
        <strong>${item.paciente_nome}</strong>
        <span class="mensagem-discreta">${item.condicao_investigada}</span>
      </div>
      <span class="mensagem-discreta">${formatarDataHora(item.criado_em)}</span>
      <div>
        <a href="anamnese.html?consulta_id=${item.consulta_id}" class="link-acao">Conduzir anamnese</a>
        <a href="heredograma.html?consulta_id=${item.consulta_id}" class="link-acao">Ver heredograma</a>
      </div>
    `;
    container.appendChild(linha);
  }
}

async function carregarResumo() {
  try {
    const resposta = await fetchAutenticado("/dashboard/resumo");
    if (!resposta.ok) {
      throw new Error("Erro ao carregar os indicadores do painel.");
    }
    const dados = await resposta.json();

    document.getElementById("numPacientesAtivos").textContent = dados.total_pacientes_ativos;
    document.getElementById("numConsultasMes").textContent = dados.consultas_mes_atual;
    document.getElementById("numEncaminhamentosPendentes").textContent = dados.encaminhamentos_pendentes;
    document.getElementById("numExamesAguardando").textContent = dados.exames_aguardando;

    renderizarAtividadeRecente(dados.atividade_recente);
  } catch (erro) {
    document.getElementById("listaAtividadeRecente").innerHTML = `<p class="erro">Erro: ${erro.message}</p>`;
  }
}

carregarResumo();
