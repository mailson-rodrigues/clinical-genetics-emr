// =====================================================================
// Verifica permissão antes de mostrar qualquer conteúdo
// =====================================================================
function verificarPermissao() {
  if (!ehAdministrador()) {
    document.getElementById("avisoAcessoNegado").style.display = "block";
    return false;
  }
  document.getElementById("conteudoCatalogos").style.display = "block";
  return true;
}

// =====================================================================
// CID
// =====================================================================
function obterFiltrosCid() {
  return {
    busca: document.getElementById("buscaCid").value,
    versao: document.getElementById("filtroVersaoCid").value,
  };
}

async function carregarCids({ busca = "", versao = "" } = {}) {
  const corpo = document.getElementById("corpoTabelaCid");
  corpo.innerHTML = "<tr><td colspan='4'>Carregando...</td></tr>";

  const parametros = new URLSearchParams();
  if (busca) parametros.set("busca", busca);
  if (versao) parametros.set("versao", versao);
  const url = parametros.toString() ? `/cids/?${parametros}` : "/cids/";

  try {
    const resposta = await fetchAutenticado(url);
    if (!resposta.ok) {
      const erro = await resposta.json().catch(() => ({}));
      throw new Error(erro.detail || "Erro ao carregar códigos CID.");
    }

    const cids = await resposta.json();

    if (cids.length === 0) {
      corpo.innerHTML = "<tr><td colspan='4'>Nenhum código CID encontrado.</td></tr>";
      return;
    }

    corpo.innerHTML = "";
    for (const cid of cids) {
      const linha = document.createElement("tr");
      linha.innerHTML = `
        <td><span class="codigo-clinico">${cid.codigo}</span></td>
        <td>${cid.descricao}</td>
        <td>${cid.capitulo || "-"}</td>
        <td>${cid.versao}</td>
      `;
      corpo.appendChild(linha);
    }
  } catch (erro) {
    corpo.innerHTML = `<tr><td colspan='4'>Erro: ${erro.message}</td></tr>`;
  }
}

document.getElementById("formCid").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const mensagem = document.getElementById("mensagemCid");
  mensagem.textContent = "";

  const corpo = {
    codigo: document.getElementById("codigoCid").value,
    descricao: document.getElementById("descricaoCid").value,
    capitulo: document.getElementById("capituloCid").value || null,
    versao: document.getElementById("versaoCid").value,
  };

  try {
    const resposta = await fetchAutenticado("/cids/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    });

    if (!resposta.ok) {
      const erro = await resposta.json();
      throw new Error(erro.detail || "Erro ao cadastrar CID.");
    }

    document.getElementById("formCid").reset();
    mensagem.textContent = "CID cadastrado com sucesso!";
    mensagem.className = "sucesso";
    carregarCids(obterFiltrosCid());
  } catch (erro) {
    mensagem.textContent = erro.message;
    mensagem.className = "erro";
  }
});

// Busca com um pequeno debounce - evita uma requisição por tecla digitada.
let timeoutBuscaCid = null;
document.getElementById("buscaCid").addEventListener("input", () => {
  clearTimeout(timeoutBuscaCid);
  timeoutBuscaCid = setTimeout(() => carregarCids(obterFiltrosCid()), 300);
});

document.getElementById("filtroVersaoCid").addEventListener("change", () => {
  carregarCids(obterFiltrosCid());
});

// =====================================================================
// Operadoras
// =====================================================================
async function carregarOperadoras() {
  const corpo = document.getElementById("corpoTabelaOperadora");
  corpo.innerHTML = "<tr><td>Carregando...</td></tr>";

  try {
    const resposta = await fetchAutenticado("/operadoras/");
    if (!resposta.ok) {
      const erro = await resposta.json().catch(() => ({}));
      throw new Error(erro.detail || "Erro ao carregar operadoras.");
    }

    const operadoras = await resposta.json();

    if (operadoras.length === 0) {
      corpo.innerHTML = "<tr><td>Nenhuma operadora cadastrada.</td></tr>";
      return;
    }

    corpo.innerHTML = "";
    for (const operadora of operadoras) {
      const linha = document.createElement("tr");
      linha.innerHTML = `<td>${operadora.nome}</td>`;
      corpo.appendChild(linha);
    }
  } catch (erro) {
    corpo.innerHTML = `<tr><td>Erro: ${erro.message}</td></tr>`;
  }
}

document.getElementById("formOperadora").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const mensagem = document.getElementById("mensagemOperadora");
  mensagem.textContent = "";

  const corpo = {
    nome: document.getElementById("nomeOperadora").value,
  };

  try {
    const resposta = await fetchAutenticado("/operadoras/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    });

    if (!resposta.ok) {
      const erro = await resposta.json();
      throw new Error(erro.detail || "Erro ao cadastrar operadora.");
    }

    document.getElementById("formOperadora").reset();
    mensagem.textContent = "Operadora cadastrada com sucesso!";
    mensagem.className = "sucesso";
    carregarOperadoras();
  } catch (erro) {
    mensagem.textContent = erro.message;
    mensagem.className = "erro";
  }
});

// =====================================================================
// Inicialização
// =====================================================================
if (verificarPermissao()) {
  carregarCids();
  carregarOperadoras();
}
