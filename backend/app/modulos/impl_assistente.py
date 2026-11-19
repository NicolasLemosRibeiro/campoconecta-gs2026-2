"""Encaixe no contrato de módulos do CampoConecta."""
import re
from dataclasses import dataclass

from ..pipelines.anonimizacao import anonimizar
from ..schemas.modulos import AssistenteEntrada, AssistenteSaida, Fonte
from .defesa_civil import generator
from .defesa_civil.retrieval import GENERICO, LIMIAR, Resultado, indice, ingerir, normalizar, tokens

ATAQUE = re.compile(
    r"\b(?:prompt|system message|developer message|jailbreak|api.?key|senha|credenciais|gemini_api_key)\b"
    r"|\b(?:ignore|desconsidere|esqueca|quebre)\b.{0,90}\b(?:instruco(?:es|ao)|regra[s]?|ordem)\b"
)
EMERGENCIA = re.compile(
    r"\b(?:ilhado[s]?|ilhada[s]?|afogando|arrastad[oa]s?|pessoa[s]? presa[s]?|pres[oa]s? pela agua"
    r"|sem saida|agua (?:esta |ta )?(?:entrando|subindo) (?:em casa|na minha casa|dentro de casa|rapido))\b"
)
TEMPO_REAL = re.compile(
    r"\b(?:previsao|agora|amanha|hoje|tempo real|horario|qual (?:a |o )?profundidade|"
    r"qual (?:abrigo|ponte|rua)|interditad[ao]|abrigos? abert[oa]s?|alerta ativo|"
    r"ja (?:liberaram|reabriu|e seguro)|aqui (?:vai|esta))\b"
)
FORA_ESCOPO = re.compile(r"\b(?:lagarta|pesticida|agrotoxico|pronaf|credito rural|bolo|futebol)\b")
SEM_EVIDENCIA = re.compile(r"\b(?:indenizacao|ressarcimento|apolice|seguro (?:de|do|rural|residencial)|precipitou|milimetros|potabilidade|"
                           r"quanto (?:de )?cloro|quanto (?:de )?hipoclorito|quantas horas|"
                           r"(?:produto|concentracao|dose|dosagem).{0,120}\b(?:potavel|cloro|hipoclorito|poco))\b")
SEGUIMENTO = re.compile(r"^(?:e\s+)?(?:a pe|de (?:carro|moto|bicicleta)|e se eu estiver a pe)\W*$")
PEDIR_DETALHE = re.compile(r"^(?:e )?(?:agora o que faco|e agora|o que faco|e depois|e se acontecer|como faco|e agora o que faco)\W*$")
CEP = re.compile(r"\b\d{5}-?\d{3}\b")
ENDERECO = re.compile(r"\b(?:rua|avenida|travessa|alameda|estrada)\s+[^,;!?\n]{2,70}?\s*,?\s+(?:n[º°o.]?\s*)?\d{1,6}\b", re.I)
MARCADORES = re.compile(r"\[(?:CPF|EMAIL|TELEFONE|PLACA|NOME|CEP|ENDEREÇO)\]")

ORIENTACOES = {
    "falta_evidencia": "A base não contém orientação suficiente para essa pergunta. A Defesa Civil do município pode orientar pelo 199.",
    "fora_escopo": "Posso orientar sobre prevenção, alertas e cuidados ligados a chuvas, enchentes e alagamentos.",
    "tempo_real": "Não consigo verificar condições atuais, alertas ativos, interdições ou abrigos. Consulte os canais oficiais da Defesa Civil e da prefeitura do seu município.",
    "ambigua": "Você quer saber como se preparar, como agir durante um alagamento ou o que fazer depois que a água baixar?",
    "instrucao_bloqueada": "Posso ajudar com orientações públicas da Defesa Civil sobre chuvas, enchentes e alagamentos.",
}


@dataclass(frozen=True)
class Atendimento:
    saida: AssistenteSaida
    consulta: str
    recuperados: list[Resultado]
    enviados: list[str]
    proposta: str | None = None


def _anonimizar(texto: str) -> str:
    return CEP.sub("[CEP]", ENDERECO.sub("[ENDEREÇO]", anonimizar(texto)))


def _fonte(trecho) -> Fonte:
    return Fonte(doc_id=trecho.id, titulo=trecho.titulo, trecho=trecho.texto, url=trecho.url,
                 secao=trecho.secao, consultado_em=trecho.consultado_em)


def _abster(motivo: str, pergunta: str, consulta: str, recuperados=None, enviados=None,
            modo="regra", proposta=None) -> Atendimento:
    return Atendimento(AssistenteSaida(
        resposta=ORIENTACOES.get(motivo, ORIENTACOES["falta_evidencia"]),
        abstencao=True, modo=modo, motivo=motivo, pergunta_exibida=pergunta,
    ), consulta, recuperados or [], enviados or [], proposta)


def _contextualizar(pergunta: str, historico: list[dict]) -> str:
    if not SEGUIMENTO.fullmatch(normalizar(pergunta)):
        return pergunta
    for turno in reversed(historico):
        anterior = turno.get("content")
        if turno.get("role") != "user" or not isinstance(anterior, str):
            continue
        anterior = _anonimizar(anterior[:500])
        plano = normalizar(anterior)
        if ATAQUE.search(plano) or TEMPO_REAL.search(plano):
            break
        if {"rua", "ponte", "alagamento", "enchente", "inundacao"}.intersection(tokens(anterior)):
            return "Travessia de via com água de alagamento. " + pergunta
        break
    return pergunta


def atender(entrada: AssistenteEntrada) -> Atendimento:
    pergunta = _anonimizar(entrada.pergunta)
    simples = normalizar(pergunta)
    if EMERGENCIA.search(simples):
        trecho = next(t for t in ingerir() if t.id == "emergencia")
        return Atendimento(AssistenteSaida(
            resposta=trecho.texto,
            fontes=[_fonte(trecho)], modo="emergencia", motivo="perigo_imediato",
            pergunta_exibida=pergunta,
        ), pergunta, [Resultado(trecho, 0)], [])
    for regex, motivo in ((ATAQUE, "instrucao_bloqueada"), (FORA_ESCOPO, "fora_escopo"),
                          (TEMPO_REAL, "tempo_real"), (SEM_EVIDENCIA, "falta_evidencia")):
        if regex.search(simples):
            return _abster(motivo, pergunta, pergunta)
    consulta = _contextualizar(pergunta, entrada.historico)
    if PEDIR_DETALHE.fullmatch(simples) or (SEGUIMENTO.fullmatch(simples) and consulta == pergunta):
        return _abster("ambigua", pergunta, consulta)

    consulta = MARCADORES.sub("", consulta)
    busca = indice()
    recuperados = busca.buscar(consulta)
    termos = set(tokens(consulta)) - GENERICO
    ancoras = termos.intersection(busca.idf)
    if not ancoras:
        motivo = "ambigua" if set(tokens(consulta)).intersection(GENERICO) else "fora_escopo"
        return _abster(motivo, pergunta, consulta, recuperados)
    candidatos = [r.trecho for r in recuperados if r.score >= LIMIAR
                  and ancoras.intersection(tokens(r.trecho.indice))]
    if not candidatos:
        return _abster("falta_evidencia", pergunta, consulta, recuperados)
    selecao = generator.selecionar(consulta, candidatos)
    enviados = [t.id for t in candidatos]
    if selecao.trecho is None:
        return _abster(selecao.motivo, pergunta, consulta, recuperados, enviados,
                       selecao.modo, selecao.proposta)
    # O fallback só publica trechos que a busca distinguiu com evidência lexical clara.
    if selecao.modo == "extrativo" and (recuperados[0].score < 2.8 or
            (len(recuperados) > 1 and recuperados[0].score - recuperados[1].score < 0.4)):
        return _abster("falta_evidencia", pergunta, consulta, recuperados, modo="extrativo")
    trecho = selecao.trecho
    return Atendimento(AssistenteSaida(
        resposta=trecho.texto, fontes=[_fonte(trecho)], modo=selecao.modo,
        motivo=selecao.motivo, pergunta_exibida=pergunta,
    ), consulta, recuperados, enviados if selecao.modo == "llm" else [], selecao.proposta)


def disponivel() -> bool:
    return bool(ingerir())


def perguntar(entrada: AssistenteEntrada) -> AssistenteSaida:
    return atender(entrada).saida
