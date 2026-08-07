// =====================================================================
// Anexos (documentos, laudos em PDF, imagens) - compartilhado por
// paciente-editar.js (um paciente) e exames.js (um exame por vez,
// painel expansível na tabela). Inclua ANTES do script específico da
// página, depois de auth.js.
// =====================================================================

function formatarTamanhoArquivo(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

function formatarDataAnexo(iso) {
  return new Date(iso).toLocaleString("pt-BR");
}

// =====================================================================
// Baixa o arquivo via fetchAutenticado (o link não pode ser um <a
// href> simples - a rota de download exige login, e um clique de link
// comum não envia o header Authorization) e dispara o download no
// navegador via um link temporário, mesmo padrão já usado para
// PDF/PNG em exportar-heredograma.js.
// =====================================================================
async function baixarAnexo(anexoId, nomeSugerido) {
  try {
    const resposta = await fetchAutenticado(`/anexos/${anexoId}/download`);
    if (!resposta.ok) {
      throw new Error("Erro ao baixar o arquivo.");
    }
    const blob = await resposta.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = nomeSugerido;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (erro) {
    alert(erro.message);
  }
}

function renderizarListaAnexos(containerEl, anexos, aoRemover) {
  if (anexos.length === 0) {
    containerEl.innerHTML = '<p class="mensagem-discreta">Nenhum documento anexado ainda.</p>';
    return;
  }

  containerEl.innerHTML = "";
  const lista = document.createElement("ul");
  lista.className = "lista-anexos";

  for (const anexo of anexos) {
    const item = document.createElement("li");
    item.className = "item-anexo";
    item.innerHTML = `
      <span class="item-anexo-nome">${anexo.nome_original}</span>
      <span class="mensagem-discreta">${formatarTamanhoArquivo(anexo.tamanho_bytes)} - ${formatarDataAnexo(anexo.criado_em)}</span>
      <span>
        <button type="button" class="link-acao item-anexo-baixar" data-baixar-anexo="${anexo.id}" data-nome-anexo="${anexo.nome_original}">Baixar</button>
        <button type="button" class="link-botao" data-remover-anexo="${anexo.id}">Remover</button>
      </span>
    `;
    lista.appendChild(item);
  }
  containerEl.appendChild(lista);

  lista.querySelectorAll("[data-baixar-anexo]").forEach((botao) => {
    botao.addEventListener("click", () => {
      baixarAnexo(botao.dataset.baixarAnexo, botao.dataset.nomeAnexo);
    });
  });

  lista.querySelectorAll("[data-remover-anexo]").forEach((botao) => {
    botao.addEventListener("click", () => aoRemover(botao.dataset.removerAnexo));
  });
}

// =====================================================================
// Liga o formulário de upload + a lista de um contexto (paciente ou
// exame) a uma rota base (`${baseUrl}/anexos`) - carrega a lista já na
// inicialização.
// =====================================================================
function inicializarAnexos({ baseUrl, formId, inputId, mensagemId, listaId }) {
  const form = document.getElementById(formId);
  const input = document.getElementById(inputId);
  const mensagem = document.getElementById(mensagemId);
  const lista = document.getElementById(listaId);

  async function carregar() {
    lista.innerHTML = "<p>Carregando...</p>";
    try {
      const resposta = await fetchAutenticado(`${baseUrl}/anexos`);
      if (!resposta.ok) throw new Error("Erro ao carregar anexos.");
      const anexos = await resposta.json();

      renderizarListaAnexos(lista, anexos, async (anexoId) => {
        const confirmou = confirm("Remover este anexo? Esta ação não pode ser desfeita.");
        if (!confirmou) return;

        const respostaRemover = await fetchAutenticado(`/anexos/${anexoId}`, { method: "DELETE" });
        if (!respostaRemover.ok) {
          alert("Erro ao remover anexo.");
          return;
        }
        carregar();
      });
    } catch (erro) {
      lista.innerHTML = `<p class="erro">Erro: ${erro.message}</p>`;
    }
  }

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    mensagem.textContent = "";

    const arquivo = input.files[0];
    if (!arquivo) {
      mensagem.textContent = "Selecione um arquivo.";
      mensagem.className = "erro";
      return;
    }

    const dadosFormulario = new FormData();
    dadosFormulario.append("arquivo", arquivo);

    try {
      // Sem header Content-Type manual - o navegador define
      // multipart/form-data com o boundary correto sozinho quando o
      // corpo é um FormData.
      const resposta = await fetchAutenticado(`${baseUrl}/anexos`, {
        method: "POST",
        body: dadosFormulario,
      });

      if (!resposta.ok) {
        const erro = await resposta.json();
        throw new Error(erro.detail || "Erro ao enviar arquivo.");
      }

      form.reset();
      mensagem.textContent = "Arquivo enviado com sucesso!";
      mensagem.className = "sucesso";
      carregar();
    } catch (erro) {
      mensagem.textContent = erro.message;
      mensagem.className = "erro";
    }
  });

  carregar();
}
