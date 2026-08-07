let modulosDisponiveis = [];

// =====================================================================
// Verifica permissão antes de mostrar qualquer conteúdo
// =====================================================================
function verificarPermissao() {
  if (!ehAdministrador()) {
    document.getElementById("avisoAcessoNegado").style.display = "block";
    return false;
  }
  document.getElementById("conteudoPerfis").style.display = "block";
  return true;
}

// =====================================================================
// Carrega o catálogo de módulos (usado para montar os checkboxes)
// =====================================================================
async function carregarModulos() {
  const resposta = await fetchAutenticado("/modulos/");
  modulosDisponiveis = await resposta.json();
}

// =====================================================================
// Carrega e renderiza os perfis cadastrados, cada um com checkboxes
// dos módulos disponíveis (marcados conforme já vinculados)
// =====================================================================
async function carregarPerfis() {
  const container = document.getElementById("listaPerfis");
  container.innerHTML = "Carregando...";

  const resposta = await fetchAutenticado("/perfis-acesso/");
  const perfis = await resposta.json();

  if (perfis.length === 0) {
    container.innerHTML = "<p>Nenhum perfil de acesso cadastrado ainda.</p>";
    return;
  }

  container.innerHTML = "";
  for (const perfil of perfis) {
    const idsVinculados = new Set(perfil.modulos.map((modulo) => modulo.id));

    const checkboxesHtml = modulosDisponiveis
      .map(
        (modulo) => `
          <label class="campo-checkbox">
            <input
              type="checkbox"
              data-perfil-id="${perfil.id}"
              data-modulo-id="${modulo.id}"
              ${idsVinculados.has(modulo.id) ? "checked" : ""}
            >
            ${modulo.nome}
          </label>
        `
      )
      .join("");

    const cartao = document.createElement("section");
    cartao.className = "cartao";
    cartao.innerHTML = `
      <h3>${perfil.nome}</h3>
      <p>${perfil.descricao || ""}</p>
      <div>${checkboxesHtml}</div>
      <button type="button" class="botao-secundario" data-remover-perfil="${perfil.id}">Remover perfil</button>
      <span id="mensagemPerfil${perfil.id}"></span>
    `;
    container.appendChild(cartao);
  }

  container.querySelectorAll("input[type=checkbox]").forEach((checkbox) => {
    checkbox.addEventListener("change", () => alternarModulo(checkbox));
  });

  container.querySelectorAll("[data-remover-perfil]").forEach((botao) => {
    botao.addEventListener("click", () => removerPerfil(botao.dataset.removerPerfil));
  });
}

// =====================================================================
// Vincula/desvincula um módulo ao marcar/desmarcar o checkbox
// =====================================================================
async function alternarModulo(checkbox) {
  const perfilId = checkbox.dataset.perfilId;
  const moduloId = Number(checkbox.dataset.moduloId);

  try {
    let resposta;
    if (checkbox.checked) {
      resposta = await fetchAutenticado(`/perfis-acesso/${perfilId}/modulos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ modulo_id: moduloId }),
      });
    } else {
      resposta = await fetchAutenticado(`/perfis-acesso/${perfilId}/modulos/${moduloId}`, {
        method: "DELETE",
      });
    }

    if (!resposta.ok) {
      const erro = await resposta.json().catch(() => ({}));
      throw new Error(erro.detail || "Erro ao atualizar módulo do perfil.");
    }
  } catch (erro) {
    alert(erro.message);
    checkbox.checked = !checkbox.checked; // reverte a marcação visualmente
  }
}

// =====================================================================
// Remove um perfil (bloqueado pelo backend se houver profissional vinculado)
// =====================================================================
async function removerPerfil(perfilId) {
  const confirmou = confirm("Remover este perfil de acesso?");
  if (!confirmou) return;

  try {
    const resposta = await fetchAutenticado(`/perfis-acesso/${perfilId}`, { method: "DELETE" });

    if (!resposta.ok) {
      const erro = await resposta.json().catch(() => ({}));
      throw new Error(erro.detail || "Erro ao remover perfil.");
    }

    carregarPerfis();
  } catch (erro) {
    alert(erro.message);
  }
}

// =====================================================================
// Cria um novo perfil de acesso
// =====================================================================
document.getElementById("formPerfil").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const mensagem = document.getElementById("mensagemPerfil");
  mensagem.textContent = "";

  const corpo = {
    nome: document.getElementById("nomePerfil").value,
    descricao: document.getElementById("descricaoPerfil").value || null,
  };

  try {
    const resposta = await fetchAutenticado("/perfis-acesso/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    });

    if (!resposta.ok) {
      const erro = await resposta.json();
      throw new Error(erro.detail || "Erro ao criar perfil.");
    }

    document.getElementById("formPerfil").reset();
    mensagem.textContent = "Perfil criado com sucesso!";
    mensagem.className = "sucesso";
    carregarPerfis();
  } catch (erro) {
    mensagem.textContent = erro.message;
    mensagem.className = "erro";
  }
});

// =====================================================================
// Inicialização
// =====================================================================
if (verificarPermissao()) {
  carregarModulos().then(carregarPerfis);
}
