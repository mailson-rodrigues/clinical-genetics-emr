function obterParametroURL(nome) {
  const parametros = new URLSearchParams(window.location.search);
  return parametros.get(nome);
}

const consultaId = obterParametroURL("consulta_id");

async function carregarRoteiro() {
  const container = document.getElementById("roteiroContainer");
  const tituloConsulta = document.getElementById("tituloConsulta");

  if (!consultaId) {
    tituloConsulta.textContent = "Nenhuma consulta selecionada.";
    container.innerHTML = "";
    return;
  }

  const [respostaPerguntas, respostaConsulta] = await Promise.all([
    fetch("/perguntas/"),
    fetch(`/consultas/${consultaId}`),
  ]);

  if (!respostaConsulta.ok) {
    tituloConsulta.textContent = "Consulta não encontrada.";
    container.innerHTML = "";
    return;
  }

  const perguntas = await respostaPerguntas.json();
  const consulta = await respostaConsulta.json();

  tituloConsulta.textContent = `Consulta #${consulta.id} — ${consulta.condicao_investigada}`;

  const respostasPorPergunta = {};
  for (const resposta of consulta.respostas) {
    respostasPorPergunta[resposta.pergunta_id] = resposta;
  }

  const categorias = {};
  for (const pergunta of perguntas) {
    if (!categorias[pergunta.categoria]) categorias[pergunta.categoria] = [];
    categorias[pergunta.categoria].push(pergunta);
  }

  container.innerHTML = "";
  for (const [categoria, listaPerguntas] of Object.entries(categorias)) {
    const tituloCategoria = document.createElement("h3");
    tituloCategoria.textContent = categoria;
    container.appendChild(tituloCategoria);

    for (const pergunta of listaPerguntas) {
      const jaRespondida = respostasPorPergunta[pergunta.id];
      const bloco = document.createElement("div");
      bloco.className = "pergunta-bloco";
      bloco.id = `bloco-pergunta-${pergunta.id}`;

      if (jaRespondida) {
        renderizarModoLeitura(bloco, pergunta, jaRespondida);
      } else {
        renderizarModoNovaResposta(bloco, pergunta);
      }

      container.appendChild(bloco);
    }
  }
}

function renderizarModoLeitura(bloco, pergunta, resposta) {
  bloco.innerHTML = `
    <p class="pergunta-texto">${pergunta.texto}</p>
    <p class="resposta-registrada">✔ ${resposta.resposta_texto}</p>
    <button type="button" class="botao-secundario" data-acao="editar" data-resposta-id="${resposta.id}" data-pergunta-id="${pergunta.id}">
      Editar
    </button>
  `;

  const botaoEditar = bloco.querySelector('[data-acao="editar"]');
  botaoEditar.addEventListener("click", () => {
    renderizarModoEdicao(bloco, pergunta, resposta);
  });
}

function renderizarModoEdicao(bloco, pergunta, resposta) {
  bloco.innerHTML = `
    <p class="pergunta-texto">${pergunta.texto}</p>
    <textarea id="edicao-${resposta.id}" rows="2">${resposta.resposta_texto}</textarea>
    <button type="button" class="botao-secundario" data-acao="salvar-edicao" data-resposta-id="${resposta.id}">
      Salvar alteração
    </button>
    <button type="button" class="botao-secundario" data-acao="cancelar-edicao">
      Cancelar
    </button>
    <span class="mensagem-edicao"></span>
  `;

  bloco.querySelector('[data-acao="salvar-edicao"]').addEventListener("click", () => {
    salvarEdicaoResposta(resposta.id, pergunta.id);
  });

  bloco.querySelector('[data-acao="cancelar-edicao"]').addEventListener("click", () => {
    renderizarModoLeitura(bloco, pergunta, resposta);
  });
}

function renderizarModoNovaResposta(bloco, pergunta) {
  bloco.innerHTML = `
    <p class="pergunta-texto">${pergunta.texto}</p>
    <textarea id="resposta-${pergunta.id}" rows="2" placeholder="Digite a resposta..."></textarea>
    <button type="button" class="botao-secundario" data-acao="salvar-nova" data-pergunta-id="${pergunta.id}">
      Salvar resposta
    </button>
  `;

  bloco.querySelector('[data-acao="salvar-nova"]').addEventListener("click", () => {
    salvarNovaResposta(pergunta.id);
  });
}

async function salvarNovaResposta(perguntaId) {
  const textarea = document.getElementById(`resposta-${perguntaId}`);
  const texto = textarea.value.trim();

  if (!texto) {
    alert("Digite uma resposta antes de salvar.");
    return;
  }

  const resposta = await fetchAutenticado(`/consultas/${consultaId}/respostas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      pergunta_id: Number(perguntaId),
      resposta_texto: texto,
    }),
  });

  if (!resposta.ok) {
    const erro = await resposta.json();
    alert(erro.detail || "Erro ao salvar resposta.");
    return;
  }

  carregarRoteiro();
}

async function salvarEdicaoResposta(respostaId, perguntaId) {
  const bloco = document.getElementById(`bloco-pergunta-${perguntaId}`);
  const textarea = document.getElementById(`edicao-${respostaId}`);
  const mensagem = bloco.querySelector(".mensagem-edicao");
  const texto = textarea.value.trim();

  if (!texto) {
    mensagem.textContent = "A resposta não pode ficar vazia.";
    mensagem.className = "mensagem-edicao erro";
    return;
  }

  const resposta = await fetchAutenticado(`/consultas/${consultaId}/respostas/${respostaId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resposta_texto: texto }),
  });

  if (!resposta.ok) {
    const erro = await resposta.json().catch(() => ({}));
    mensagem.textContent = erro.detail || "Erro ao salvar alteração.";
    mensagem.className = "mensagem-edicao erro";
    return;
  }

  carregarRoteiro();
}

document.getElementById("btnGerarHeredograma").addEventListener("click", async () => {
  const mensagem = document.getElementById("mensagemGeracao");
  const linkContainer = document.getElementById("linkHeredograma");
  mensagem.textContent = "Gerando com IA, aguarde (pode levar alguns segundos)...";
  linkContainer.innerHTML = "";

  try {
    const resposta = await fetchAutenticado(`/consultas/${consultaId}/gerar-heredograma`, {
      method: "POST",
    });

    if (!resposta.ok) {
      const erro = await resposta.json();
      throw new Error(erro.detail || "Erro ao gerar heredograma.");
    }

    mensagem.textContent = "Heredograma gerado com sucesso!";
    mensagem.className = "sucesso";
    linkContainer.innerHTML = `<a href="heredograma.html?consulta_id=${consultaId}" class="botao">Ver heredograma</a>`;
  } catch (erro) {
    mensagem.textContent = `Erro: ${erro.message}`;
    mensagem.className = "erro";
  }
});

carregarRoteiro();