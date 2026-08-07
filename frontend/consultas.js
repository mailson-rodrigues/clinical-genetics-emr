function obterParametroURL(nome) {
  const parametros = new URLSearchParams(window.location.search);
  return parametros.get(nome);
}

const pacienteId = obterParametroURL("paciente_id");

async function carregarNomePaciente() {
  const resposta = await fetch(`/pacientes/${pacienteId}`);
  if (!resposta.ok) {
    document.getElementById("nomePacienteTitulo").textContent = "Paciente não encontrado";
    return;
  }
  const paciente = await resposta.json();
  document.getElementById("nomePacienteTitulo").textContent = `Consultas de: ${paciente.nome}`;
}

async function carregarConsultas() {
  const corpo = document.getElementById("corpoTabelaConsultas");
  corpo.innerHTML = "<tr><td colspan='5'>Carregando...</td></tr>";

  const resposta = await fetch(`/consultas/?paciente_id=${pacienteId}`);
  const consultas = await resposta.json();

  if (consultas.length === 0) {
    corpo.innerHTML = "<tr><td colspan='5'>Nenhuma consulta registrada ainda.</td></tr>";
    return;
  }

  corpo.innerHTML = "";
  for (const consulta of consultas) {
    const linha = document.createElement("tr");
    linha.innerHTML = `
      <td>${consulta.id}</td>
      <td>${consulta.condicao_investigada}</td>
      <td>${consulta.status}</td>
      <td>${new Date(consulta.criado_em).toLocaleString("pt-BR")}</td>
      <td>
        <a href="anamnese.html?consulta_id=${consulta.id}" class="link-acao">Conduzir anamnese</a>
        <a href="heredograma.html?consulta_id=${consulta.id}" class="link-acao">Ver heredograma</a>
        <a href="hipoteses.html?consulta_id=${consulta.id}" class="link-acao">Hipóteses</a>
        <a href="encaminhamentos.html?consulta_id=${consulta.id}" class="link-acao">Encaminhamentos</a>
        <a href="exames.html?consulta_id=${consulta.id}" class="link-acao">Exames</a>
      </td>
    `;
    corpo.appendChild(linha);
  }
}

document.getElementById("formConsulta").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const mensagem = document.getElementById("mensagemConsulta");
  mensagem.textContent = "";

  const corpo = {
    paciente_id: Number(pacienteId),
    condicao_investigada: document.getElementById("condicao").value,
  };

  try {
    const resposta = await fetchAutenticado("/consultas/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    });

    if (!resposta.ok) {
      const erro = await resposta.json();
      throw new Error(erro.detail || "Erro ao criar consulta.");
    }

    const novaConsulta = await resposta.json();
    window.location.href = `anamnese.html?consulta_id=${novaConsulta.id}`;
  } catch (erro) {
    mensagem.textContent = erro.message;
    mensagem.className = "erro";
  }
});

if (!pacienteId) {
  document.getElementById("nomePacienteTitulo").textContent = "Nenhum paciente selecionado.";
} else {
  carregarNomePaciente();
  carregarConsultas();
}