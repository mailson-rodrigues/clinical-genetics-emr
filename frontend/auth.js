// =====================================================================
// Utilitário de autenticação, compartilhado por todas as páginas.
// Deve ser incluído ANTES do script específico de cada página.
// =====================================================================

const CHAVE_TOKEN = "heredograma_ia_token";
const CHAVE_NOME = "heredograma_ia_nome";
const CHAVE_NIVEL_ACESSO = "heredograma_ia_nivel_acesso";
const CHAVE_PROFISSIONAL_ID = "heredograma_ia_profissional_id";

function salvarSessao(token, nome, nivelAcesso, profissionalId) {
  localStorage.setItem(CHAVE_TOKEN, token);
  localStorage.setItem(CHAVE_NOME, nome);
  localStorage.setItem(CHAVE_NIVEL_ACESSO, nivelAcesso || "profissional");
  localStorage.setItem(CHAVE_PROFISSIONAL_ID, profissionalId);
}

function obterToken() {
  return localStorage.getItem(CHAVE_TOKEN);
}

function obterNomeUsuario() {
  return localStorage.getItem(CHAVE_NOME);
}

function obterNivelAcesso() {
  return localStorage.getItem(CHAVE_NIVEL_ACESSO) || "profissional";
}

function ehAdministrador() {
  return obterNivelAcesso() === "administrador";
}

function limparSessao() {
  localStorage.removeItem(CHAVE_TOKEN);
  localStorage.removeItem(CHAVE_NOME);
  localStorage.removeItem(CHAVE_NIVEL_ACESSO);
  localStorage.removeItem(CHAVE_PROFISSIONAL_ID);
}

function estaLogado() {
  return Boolean(obterToken());
}

function exigirLogin() {
  if (!estaLogado()) {
    window.location.href = "login.html";
  }
}

function fazerLogout() {
  limparSessao();
  window.location.href = "login.html";
}

async function fetchAutenticado(url, opcoes = {}) {
  const token = obterToken();
  const cabecalhos = {
    ...(opcoes.headers || {}),
    Authorization: `Bearer ${token}`,
  };

  const resposta = await fetch(url, { ...opcoes, headers: cabecalhos });

  if (resposta.status === 401) {
    limparSessao();
    window.location.href = "login.html";
    throw new Error("Sessão expirada. Faça login novamente.");
  }

  return resposta;
}

// =====================================================================
// Injeta os links do grupo "Configuração" na barra lateral
// (#grupoConfiguracao, ver *.html), visíveis só para administradores -
// evita precisar editar a sidebar de cada página HTML manualmente
// sempre que criamos uma tela restrita a admin. Lista de links (em vez
// de um único link fixo) para não precisar duplicar essa lógica a cada
// nova tela admin-only (ex: Logs, Perfis, Catálogos).
// =====================================================================
const LINKS_CONFIGURACAO_SIDEBAR = [
  { href: "profissionais.html", texto: "Profissionais" },
  { href: "perfis.html", texto: "Perfis de Acesso" },
  { href: "catalogos.html", texto: "Catálogos" },
  { href: "logs.html", texto: "Logs de Auditoria" },
];

function montarSidebarConfiguracao() {
  const grupo = document.getElementById("grupoConfiguracao");
  if (!grupo) return;
  if (!ehAdministrador()) return;

  for (const link of LINKS_CONFIGURACAO_SIDEBAR) {
    const elementoLink = document.createElement("a");
    elementoLink.href = link.href;
    elementoLink.textContent = link.texto;
    if (window.location.pathname.endsWith(link.href)) {
      elementoLink.className = "ativo";
    }
    grupo.appendChild(elementoLink);
  }

  grupo.hidden = false;
}

// =====================================================================
// Menu hambúrguer (mobile) da barra lateral.
// =====================================================================
function inicializarMenuMobile() {
  const botao = document.getElementById("btnMenuMobile");
  const sidebar = document.getElementById("sidebar");
  if (!botao || !sidebar) return;

  botao.addEventListener("click", () => {
    const aberto = sidebar.classList.toggle("sidebar-aberta");
    botao.setAttribute("aria-expanded", String(aberto));
  });

  sidebar.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      sidebar.classList.remove("sidebar-aberta");
      botao.setAttribute("aria-expanded", "false");
    });
  });
}

function inicializarBarraUsuario() {
  const elementoNome = document.getElementById("nomeUsuarioLogado");
  if (elementoNome) {
    elementoNome.textContent = obterNomeUsuario() || "";
  }

  const botaoLogout = document.getElementById("btnLogout");
  if (botaoLogout) {
    botaoLogout.addEventListener("click", fazerLogout);
  }

  montarSidebarConfiguracao();
  inicializarMenuMobile();
}