async function carregarEspecialidades() {
  const select = document.getElementById("especialidade");
  const resposta = await fetch("/especialidades/");
  const especialidades = await resposta.json();

  // innerHTML fixo (não appendChild) - esta função é chamada de novo
  // depois de cadastrar uma especialidade pelo modal (ver
  // formNovaEspecialidade abaixo), então precisa ser seguro rodar mais
  // de uma vez sem duplicar as opções já existentes.
  select.innerHTML = '<option value="">Não informar</option>';
  for (const especialidade of especialidades) {
    const opcao = document.createElement("option");
    opcao.value = especialidade.id;
    opcao.textContent = especialidade.nome;
    select.appendChild(opcao);
  }
}

// =====================================================================
// Modal "Nova especialidade" - cadastra direto do formulário de
// profissional, sem precisar sair da página. POST /especialidades/ não
// exige administrador hoje (ao contrário de CID/Operadora) - qualquer
// profissional logado pode cadastrar; usamos fetchAutenticado mesmo
// assim, por consistência com o resto do formulário.
// =====================================================================
const modalEspecialidade = document.getElementById("modalEspecialidade");

document.getElementById("btnNovaEspecialidade").addEventListener("click", () => {
  document.getElementById("formNovaEspecialidade").reset();
  document.getElementById("mensagemNovaEspecialidade").textContent = "";
  modalEspecialidade.showModal();
  document.getElementById("nomeNovaEspecialidade").focus();
});

document.getElementById("btnCancelarNovaEspecialidade").addEventListener("click", () => {
  modalEspecialidade.close();
});

document.getElementById("formNovaEspecialidade").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const mensagem = document.getElementById("mensagemNovaEspecialidade");
  mensagem.textContent = "";

  const nome = document.getElementById("nomeNovaEspecialidade").value;

  try {
    const resposta = await fetchAutenticado("/especialidades/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nome }),
    });

    if (!resposta.ok) {
      const erro = await resposta.json();
      throw new Error(erro.detail || "Erro ao cadastrar especialidade.");
    }

    const novaEspecialidade = await resposta.json();
    await carregarEspecialidades();
    document.getElementById("especialidade").value = novaEspecialidade.id;
    modalEspecialidade.close();
  } catch (erro) {
    mensagem.textContent = erro.message;
  }
});

// =====================================================================
// Carrega os perfis de acesso para o <select> do formulário. A rota é
// restrita a administrador - se quem está usando a página ainda não
// tem sessão de admin (ex: cadastrando o primeiro administrador do
// sistema), a busca falha silenciosamente e o campo fica desabilitado,
// sem travar o resto da página. Usa fetch simples (não
// fetchAutenticado) para evitar o redirecionamento automático em caso
// de 401 nesse cenário de bootstrap.
// =====================================================================
async function carregarPerfisAcesso() {
  const select = document.getElementById("perfilAcesso");
  try {
    const token = obterToken();
    const resposta = await fetch("/perfis-acesso/", {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!resposta.ok) {
      select.disabled = true;
      return;
    }
    const perfis = await resposta.json();
    for (const perfil of perfis) {
      const opcao = document.createElement("option");
      opcao.value = perfil.id;
      opcao.textContent = perfil.nome;
      select.appendChild(opcao);
    }
  } catch (erro) {
    select.disabled = true;
  }
}

// =====================================================================
// O perfil de acesso só se aplica a profissionais não-administradores
// (administrador tem acesso total, sem precisar de perfil).
// =====================================================================
function atualizarVisibilidadePerfilAcesso() {
  const nivel = document.getElementById("nivelAcesso").value;
  const campoPerfil = document.getElementById("campoPerfilAcesso");
  const selectPerfil = document.getElementById("perfilAcesso");

  if (nivel === "administrador") {
    campoPerfil.style.display = "none";
    selectPerfil.value = "";
  } else {
    campoPerfil.style.display = "";
  }
}

document.getElementById("nivelAcesso").addEventListener("change", atualizarVisibilidadePerfilAcesso);

async function carregarProfissionais() {
  const corpo = document.getElementById("corpoTabelaProfissionais");
  corpo.innerHTML = "<tr><td colspan='7'>Carregando...</td></tr>";

  const token = obterToken();
  const [respostaProfissionais, respostaEspecialidades, respostaPerfis] = await Promise.all([
    fetch("/profissionais/"),
    fetch("/especialidades/"),
    // GET /perfis-acesso/ é restrita a administrador - se falhar (ex:
    // sem sessão de admin), a coluna de perfil só cai no "-" abaixo.
    fetch("/perfis-acesso/", { headers: token ? { Authorization: `Bearer ${token}` } : {} }),
  ]);

  const profissionais = await respostaProfissionais.json();
  const especialidades = await respostaEspecialidades.json();

  const nomeEspecialidadePorId = {};
  for (const especialidade of especialidades) {
    nomeEspecialidadePorId[especialidade.id] = especialidade.nome;
  }

  const nomePerfilPorIdParaTabela = {};
  if (respostaPerfis.ok) {
    const perfis = await respostaPerfis.json();
    for (const perfil of perfis) {
      nomePerfilPorIdParaTabela[perfil.id] = perfil.nome;
    }
  }

  if (profissionais.length === 0) {
    corpo.innerHTML = "<tr><td colspan='7'>Nenhum profissional cadastrado ainda.</td></tr>";
    return;
  }

  corpo.innerHTML = "";
  for (const profissional of profissionais) {
    const nomeEspecialidade = profissional.especialidade_id
      ? (nomeEspecialidadePorId[profissional.especialidade_id] || "-")
      : "-";
    const nivelFormatado = profissional.nivel_acesso === "administrador" ? "Administrador" : "Profissional";
    const nomePerfil = profissional.perfil_acesso_id
      ? (nomePerfilPorIdParaTabela[profissional.perfil_acesso_id] || "-")
      : "-";
    const linha = document.createElement("tr");
    linha.innerHTML = `
      <td>${profissional.nome}</td>
      <td>${profissional.email}</td>
      <td>${nomeEspecialidade}</td>
      <td>${profissional.registro_profissional || "-"}</td>
      <td>${nivelFormatado}</td>
      <td>${nomePerfil}</td>
      <td>${profissional.ativo ? "Ativo" : "Inativo"}</td>
    `;
    corpo.appendChild(linha);
  }
}

document.getElementById("formProfissional").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const mensagem = document.getElementById("mensagemProfissional");
  mensagem.textContent = "";

  const corpo = {
    nome: document.getElementById("nome").value,
    email: document.getElementById("email").value,
    senha: document.getElementById("senha").value,
    especialidade_id: document.getElementById("especialidade").value
      ? Number(document.getElementById("especialidade").value)
      : null,
    registro_profissional: document.getElementById("registroProfissional").value || null,
    nivel_acesso: document.getElementById("nivelAcesso").value,
    perfil_acesso_id:
      document.getElementById("nivelAcesso").value === "profissional" && document.getElementById("perfilAcesso").value
        ? Number(document.getElementById("perfilAcesso").value)
        : null,
  };

  try {
    const resposta = await fetch("/profissionais/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    });

    if (!resposta.ok) {
      const erro = await resposta.json();
      throw new Error(erro.detail || "Erro ao cadastrar profissional.");
    }

    document.getElementById("formProfissional").reset();
    mensagem.textContent = "Profissional cadastrado com sucesso!";
    mensagem.className = "sucesso";
    carregarProfissionais();
  } catch (erro) {
    mensagem.textContent = erro.message;
    mensagem.className = "erro";
  }
});

carregarEspecialidades();
carregarPerfisAcesso();
atualizarVisibilidadePerfilAcesso();
carregarProfissionais();