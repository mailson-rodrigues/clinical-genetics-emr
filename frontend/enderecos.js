// =====================================================================
// Utilitários de endereço, compartilhados por pacientes.js e
// paciente-editar.js (mesmos ids de campo: #cep, #endereco, #bairro,
// #cidade, #uf, #mensagemCep) - inclua ANTES do script específico da
// página, depois de auth.js.
// =====================================================================

const UFS = [
  { sigla: "AC", nome: "Acre" },
  { sigla: "AL", nome: "Alagoas" },
  { sigla: "AP", nome: "Amapá" },
  { sigla: "AM", nome: "Amazonas" },
  { sigla: "BA", nome: "Bahia" },
  { sigla: "CE", nome: "Ceará" },
  { sigla: "DF", nome: "Distrito Federal" },
  { sigla: "ES", nome: "Espírito Santo" },
  { sigla: "GO", nome: "Goiás" },
  { sigla: "MA", nome: "Maranhão" },
  { sigla: "MT", nome: "Mato Grosso" },
  { sigla: "MS", nome: "Mato Grosso do Sul" },
  { sigla: "MG", nome: "Minas Gerais" },
  { sigla: "PA", nome: "Pará" },
  { sigla: "PB", nome: "Paraíba" },
  { sigla: "PR", nome: "Paraná" },
  { sigla: "PE", nome: "Pernambuco" },
  { sigla: "PI", nome: "Piauí" },
  { sigla: "RJ", nome: "Rio de Janeiro" },
  { sigla: "RN", nome: "Rio Grande do Norte" },
  { sigla: "RS", nome: "Rio Grande do Sul" },
  { sigla: "RO", nome: "Rondônia" },
  { sigla: "RR", nome: "Roraima" },
  { sigla: "SC", nome: "Santa Catarina" },
  { sigla: "SP", nome: "São Paulo" },
  { sigla: "SE", nome: "Sergipe" },
  { sigla: "TO", nome: "Tocantins" },
];

function preencherSelectUf(select) {
  select.innerHTML = '<option value="">Selecione</option>';
  for (const uf of UFS) {
    const opcao = document.createElement("option");
    opcao.value = uf.sigla;
    opcao.textContent = `${uf.sigla} - ${uf.nome}`;
    select.appendChild(opcao);
  }
}

function apenasDigitos(texto) {
  return (texto || "").replace(/\D/g, "");
}

// =====================================================================
// Busca o endereço pelo CEP na API pública do ViaCEP e preenche
// Endereço/Bairro/Cidade/UF - os campos continuam editáveis depois
// (não travamos nada), para o profissional corrigir se o retorno vier
// incompleto. Falha de rede ou CEP inexistente não trava o formulário:
// só mostra um aviso discreto (sem popup) e deixa o preenchimento
// manual normal.
// =====================================================================
async function buscarEnderecoPorCep(cep) {
  const elementoMensagem = document.getElementById("mensagemCep");
  if (elementoMensagem) elementoMensagem.textContent = "";

  try {
    const resposta = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
    if (!resposta.ok) throw new Error("Falha na consulta ao CEP.");
    const dados = await resposta.json();

    if (dados.erro) {
      if (elementoMensagem) elementoMensagem.textContent = "CEP não encontrado, preencha manualmente.";
      return;
    }

    const campoEndereco = document.getElementById("endereco");
    const campoBairro = document.getElementById("bairro");
    const campoCidade = document.getElementById("cidade");
    const campoUf = document.getElementById("uf");

    if (campoEndereco && dados.logradouro) campoEndereco.value = dados.logradouro;
    if (campoBairro && dados.bairro) campoBairro.value = dados.bairro;
    if (campoCidade && dados.localidade) campoCidade.value = dados.localidade;
    if (campoUf && dados.uf) campoUf.value = dados.uf;
  } catch (erro) {
    if (elementoMensagem) elementoMensagem.textContent = "CEP não encontrado, preencha manualmente.";
  }
}

// =====================================================================
// Dispara a busca quando o campo perde o foco ou assim que atinge 8
// dígitos (permite completar via teclado sem precisar sair do campo).
// Memoriza o último CEP já consultado para não repetir a mesma busca -
// sem isso, o "input" dispara ao digitar o 8º dígito e o "blur" dispara
// de novo (mesmo CEP) ao sair do campo logo em seguida, e a resposta
// dessa segunda busca (assíncrona) pode sobrescrever uma correção
// manual que o profissional já tenha feito no meio do caminho.
// =====================================================================
let ultimoCepConsultado = null;

function inicializarBuscaCep() {
  const campoCep = document.getElementById("cep");
  if (!campoCep) return;

  const disparar = () => {
    const cep = apenasDigitos(campoCep.value);
    if (cep.length === 8 && cep !== ultimoCepConsultado) {
      ultimoCepConsultado = cep;
      buscarEnderecoPorCep(cep);
    }
  };

  campoCep.addEventListener("blur", disparar);
  campoCep.addEventListener("input", disparar);
}
