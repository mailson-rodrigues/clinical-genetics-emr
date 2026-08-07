// =====================================================================
// Verifica permissão antes de mostrar qualquer conteúdo
// =====================================================================
function verificarPermissao() {
  if (!ehAdministrador()) {
    document.getElementById("avisoAcessoNegado").style.display = "block";
    return false;
  }
  document.getElementById("conteudoLogs").style.display = "block";
  document.getElementById("tabelaContainer").style.display = "block";
  return true;
}

// =====================================================================
// Formata visualmente o status HTTP com uma classe de cor
// =====================================================================
function classePorStatus(statusCode) {
  if (!statusCode) return "";
  if (statusCode >= 200 && statusCode < 300) return "status-sucesso";
  if (statusCode === 401 || statusCode === 403) return "status-negado";
  if (statusCode >= 400) return "status-erro";
  return "";
}

// =====================================================================
// Carrega a lista de profissionais para o filtro e para exibir nomes
// (em vez de só o ID) na tabela.
// =====================================================================
let nomePorProfissionalId = {};

async function carregarProfissionaisParaFiltro() {
  const resposta = await fetch("/profissionais/");
  const profissionais = await resposta.json();

  const select = document.getElementById("filtroProfissional");
  for (const profissional of profissionais) {
    nomePorProfissionalId[profissional.id] = profissional.nome;
    const opcao = document.createElement("option");
    opcao.value = profissional.id;
    opcao.textContent = profissional.nome;
    select.appendChild(opcao);
  }
}

// =====================================================================
// Carrega e renderiza os logs, respeitando os filtros escolhidos
// =====================================================================
async function carregarLogs() {
  const corpo = document.getElementById("corpoTabelaLogs");
  corpo.innerHTML = "<tr><td colspan='5'>Carregando...</td></tr>";

  const profissionalId = document.getElementById("filtroProfissional").value;
  const limite = document.getElementById("filtroLimite").value;

  let url = `/logs/?limite=${limite}`;
  if (profissionalId) {
    url += `&profissional_id=${profissionalId}`;
  }

  try {
    const resposta = await fetchAutenticado(url);
    if (!resposta.ok) {
      const erro = await resposta.json().catch(() => ({}));
      throw new Error(erro.detail || "Erro ao carregar logs.");
    }

    const logs = await resposta.json();

    if (logs.length === 0) {
      corpo.innerHTML = "<tr><td colspan='5'>Nenhum registro encontrado.</td></tr>";
      return;
    }

    corpo.innerHTML = "";
    for (const log of logs) {
      const nomeProfissional = log.profissional_id
        ? (nomePorProfissionalId[log.profissional_id] || `ID ${log.profissional_id}`)
        : "Anônimo / sem login";
      const dataFormatada = new Date(log.criado_em).toLocaleString("pt-BR");

      const linha = document.createElement("tr");
      linha.innerHTML = `
        <td>${dataFormatada}</td>
        <td>${nomeProfissional}</td>
        <td>${log.metodo}</td>
        <td>${log.caminho}</td>
        <td class="${classePorStatus(log.status_code)}">${log.status_code ?? "-"}</td>
      `;
      corpo.appendChild(linha);
    }
  } catch (erro) {
    corpo.innerHTML = `<tr><td colspan='5'>Erro: ${erro.message}</td></tr>`;
  }
}

document.getElementById("btnFiltrar").addEventListener("click", carregarLogs);

// =====================================================================
// Inicialização
// =====================================================================
if (verificarPermissao()) {
  carregarProfissionaisParaFiltro().then(carregarLogs);
}