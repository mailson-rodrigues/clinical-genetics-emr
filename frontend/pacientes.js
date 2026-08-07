async function carregarPacientes(busca) {
  const corpo = document.getElementById("corpoTabelaPacientes");
  corpo.innerHTML = "<tr><td colspan='6'>Carregando...</td></tr>";

  const parametros = new URLSearchParams({ limit: "20" });
  if (busca) {
    parametros.set("busca", busca);
  }

  const resposta = await fetch(`/pacientes/?${parametros.toString()}`);
  const pacientes = await resposta.json();

  if (pacientes.length === 0) {
    corpo.innerHTML = busca
      ? "<tr><td colspan='6'>Nenhum paciente encontrado para essa busca.</td></tr>"
      : "<tr><td colspan='6'>Nenhum paciente cadastrado ainda.</td></tr>";
    return;
  }

  corpo.innerHTML = "";
  for (const paciente of pacientes) {
    const cidadeUf = [paciente.cidade, paciente.uf].filter(Boolean).join("/") || "-";
    const linha = document.createElement("tr");
    linha.innerHTML = `
      <td>${paciente.nome_social || paciente.nome}</td>
      <td>${paciente.data_nascimento}</td>
      <td>${paciente.sexo}</td>
      <td><span class="codigo-clinico">${paciente.documento}</span></td>
      <td>${cidadeUf}</td>
      <td>
        <a href="consultas.html?paciente_id=${paciente.id}" class="link-acao">Ver consultas</a>
        <a href="paciente-editar.html?paciente_id=${paciente.id}" class="link-acao">Editar</a>
      </td>
    `;
    corpo.appendChild(linha);
  }
}

let temporizadorBusca = null;
document.getElementById("buscaPaciente").addEventListener("input", (evento) => {
  clearTimeout(temporizadorBusca);
  const termo = evento.target.value.trim();
  temporizadorBusca = setTimeout(() => carregarPacientes(termo), 300);
});

carregarPacientes();
