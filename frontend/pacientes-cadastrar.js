document.getElementById("formPaciente").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const mensagem = document.getElementById("mensagemPaciente");
  mensagem.textContent = "";

  const corpo = {
    nome: document.getElementById("nome").value,
    nome_social: document.getElementById("nomeSocial").value || null,
    data_nascimento: document.getElementById("dataNascimento").value,
    sexo: document.getElementById("sexo").value,
    tipo_sanguineo: document.getElementById("tipoSanguineo").value || null,
    documento: document.getElementById("documento").value,
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
    const resposta = await fetch("/pacientes/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    });

    if (!resposta.ok) {
      const erro = await resposta.json();
      throw new Error(erro.detail || "Erro ao cadastrar paciente.");
    }

    mensagem.textContent = "Paciente cadastrado com sucesso! Redirecionando...";
    mensagem.className = "sucesso";
    setTimeout(() => {
      window.location.href = "pacientes.html";
    }, 900);
  } catch (erro) {
    mensagem.textContent = erro.message;
    mensagem.className = "erro";
  }
});

preencherSelectUf(document.getElementById("uf"));
inicializarBuscaCep();
