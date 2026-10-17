// =====================================================================
// Address utilities, shared by pacientes.js and
// paciente-editar.js (same field ids: #cep, #endereco, #bairro,
// #cidade, #uf, #mensagemCep) - include BEFORE the page-specific
// script, after auth.js.
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
// Looks up the address by CEP in the public ViaCEP API and fills in
// Endereço/Bairro/Cidade/UF - the fields remain editable afterwards
// (we do not lock anything), so the professional can correct it if the result is
// incomplete. A network failure or a nonexistent CEP does not freeze the form:
// it only shows a discreet notice (no popup) and leaves normal
// manual filling.
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
// Triggers the lookup when the field loses focus or as soon as it reaches 8
// digits (allows completing via keyboard without leaving the field).
// Remembers the last CEP already queried to avoid repeating the same lookup -
// without that, "input" fires when typing the 8th digit and "blur" fires
// again (same CEP) when leaving the field right after, and the response
// of that second (asynchronous) lookup could overwrite a manual
// correction the professional had already made in the meantime.
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
