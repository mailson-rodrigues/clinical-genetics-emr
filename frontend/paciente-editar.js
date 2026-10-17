function obterParametroURL(nome) {
  const parametros = new URLSearchParams(window.location.search);
  return parametros.get(nome);
}

const pacienteId = obterParametroURL("paciente_id");

// =====================================================================
// Checks permission BEFORE loading any data - prevents a
// regular professional from seeing the filled-in form only to get a
// 403 error when trying to save.
// =====================================================================
function verificarPermissao() {
  if (!ehAdministrador()) {
    document.getElementById("avisoAcessoNegado").style.display = "block";
    document.getElementById("formularioContainer").style.display = "none";
    return false;
  }
  return true;
}

// =====================================================================
// Loads the current patient data and fills in the form
// =====================================================================
async function carregarPaciente() {
  if (!pacienteId) {
    document.getElementById("mensagemEdicao").textContent = "Nenhum paciente selecionado.";
    return;
  }

  const resposta = await fetch(`/pacientes/${pacienteId}`);
  if (!resposta.ok) {
    document.getElementById("mensagemEdicao").textContent = "Paciente não encontrado.";
    document.getElementById("formularioContainer").style.display = "none";
    return;
  }

  const paciente = await resposta.json();

  document.getElementById("nome").value = paciente.nome || "";
  document.getElementById("nomeSocial").value = paciente.nome_social || "";
  document.getElementById("dataNascimento").value = paciente.data_nascimento || "";
  document.getElementById("sexo").value = paciente.sexo || "";
  document.getElementById("tipoSanguineo").value = paciente.tipo_sanguineo || "";
  document.getElementById("rg").value = paciente.rg || "";
  document.getElementById("telefone").value = paciente.telefone || "";
  document.getElementById("whatsapp").value = paciente.whatsapp || "";
  document.getElementById("email").value = paciente.email || "";
  document.getElementById("cep").value = paciente.cep || "";
  document.getElementById("endereco").value = paciente.endereco || "";
  document.getElementById("numero").value = paciente.numero || "";
  document.getElementById("complemento").value = paciente.complemento || "";
  document.getElementById("bairro").value = paciente.bairro || "";
  document.getElementById("cidade").value = paciente.cidade || "";
  document.getElementById("uf").value = paciente.uf || "";
  document.getElementById("recemNascido").checked = Boolean(paciente.recem_nascido);
  document.getElementById("nomeResponsavel").value = paciente.nome_responsavel || "";
  document.getElementById("parentescoResponsavel").value = paciente.parentesco_responsavel || "";
  document.getElementById("aceitaMensagens").checked = Boolean(paciente.aceita_mensagens);
  document.getElementById("autorizacaoLgpd").checked = Boolean(paciente.autorizacao_lgpd);

  document.getElementById("anexosContainer").style.display = "block";
  document.getElementById("zonaPerigoContainer").style.display = "block";
}

// =====================================================================
// Sends the changes (PUT - requires admin)
// =====================================================================
document.getElementById("formEditarPaciente").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const mensagem = document.getElementById("mensagemEdicao");
  mensagem.textContent = "";

  const corpo = {
    nome: document.getElementById("nome").value,
    nome_social: document.getElementById("nomeSocial").value || null,
    data_nascimento: document.getElementById("dataNascimento").value,
    sexo: document.getElementById("sexo").value,
    tipo_sanguineo: document.getElementById("tipoSanguineo").value || null,
    rg: document.getElementById("rg").value || null,
    telefone: document.getElementById("telefone").value || null,
    whatsapp: document.getElementById("whatsapp").value || null,
    email: document.getElementById("email").value || null,
    cep: document.getElementById("cep").value || null,
    endereco: document.getElementById("endereco").value || null,
    numero: document.getElementById("numero").value || null,
    complemento: document.getElementById("complemento").value || null,
    bairro: document.getElementById("bairro").value || null,
    cidade: document.getElementById("cidade").value || null,
    uf: document.getElementById("uf").value || null,
    recem_nascido: document.getElementById("recemNascido").checked,
    nome_responsavel: document.getElementById("nomeResponsavel").value || null,
    parentesco_responsavel: document.getElementById("parentescoResponsavel").value || null,
    aceita_mensagens: document.getElementById("aceitaMensagens").checked,
    autorizacao_lgpd: document.getElementById("autorizacaoLgpd").checked,
  };

  try {
    const resposta = await fetchAutenticado(`/pacientes/${pacienteId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    });

    if (!resposta.ok) {
      const erro = await resposta.json();
      throw new Error(erro.detail || "Erro ao salvar alterações.");
    }

    mensagem.textContent = "Alterações salvas com sucesso!";
    mensagem.className = "sucesso";
  } catch (erro) {
    mensagem.textContent = erro.message;
    mensagem.className = "erro";
  }
});

// =====================================================================
// Remove patient (DELETE - requires admin, with confirmation)
// =====================================================================
document.getElementById("btnRemoverPaciente").addEventListener("click", async () => {
  const confirmou = confirm(
    "Tem certeza que deseja remover este paciente? Esta ação não pode ser desfeita."
  );
  if (!confirmou) return;

  const mensagem = document.getElementById("mensagemRemocao");
  mensagem.textContent = "";

  try {
    const resposta = await fetchAutenticado(`/pacientes/${pacienteId}`, {
      method: "DELETE",
    });

    if (!resposta.ok) {
      const erro = await resposta.json().catch(() => ({}));
      throw new Error(erro.detail || "Erro ao remover paciente.");
    }

    alert("Paciente removido com sucesso.");
    window.location.href = "pacientes.html";
  } catch (erro) {
    mensagem.textContent = erro.message;
    mensagem.className = "erro";
  }
});

// =====================================================================
// Initialization
// =====================================================================
preencherSelectUf(document.getElementById("uf"));
inicializarBuscaCep();

if (verificarPermissao()) {
  carregarPaciente();
  inicializarAnexos({
    baseUrl: `/pacientes/${pacienteId}`,
    formId: "formAnexoPaciente",
    inputId: "arquivoAnexoPaciente",
    mensagemId: "mensagemAnexoPaciente",
    listaId: "listaAnexosPaciente",
  });
}