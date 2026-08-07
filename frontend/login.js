document.getElementById("formLogin").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const mensagem = document.getElementById("mensagemLogin");
  mensagem.textContent = "";

  const email = document.getElementById("email").value;
  const senha = document.getElementById("senha").value;

  try {
    const resposta = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, senha }),
    });

    if (!resposta.ok) {
      const erro = await resposta.json().catch(() => ({}));
      throw new Error(erro.detail || "Erro ao fazer login.");
    }

    const dados = await resposta.json();
    localStorage.setItem("heredograma_ia_token", dados.access_token);
    localStorage.setItem("heredograma_ia_nome", dados.nome);
    localStorage.setItem("heredograma_ia_nivel_acesso", dados.nivel_acesso || "profissional");
    localStorage.setItem("heredograma_ia_profissional_id", dados.profissional_id);
    window.location.href = "index.html";
  } catch (erro) {
    mensagem.textContent = erro.message;
    mensagem.className = "erro";
  }
});