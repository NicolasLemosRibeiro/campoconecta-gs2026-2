"""Avalia o assistente com gabarito explícito e registra cada execução em JSON."""
import argparse
import json
import os
import platform
import random
import statistics
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

from fastapi.testclient import TestClient
import requests

from app.main import app
from app.modulos import impl_assistente as assistente
from app.modulos.defesa_civil import generator
from app.modulos.defesa_civil.retrieval import indice, ingerir
from app.schemas.modulos import AssistenteEntrada

RAIZ = Path(__file__).resolve().parents[1]
ROTA = "/modulos/assistente/perguntar"
CASOS = RAIZ / "data" / "assistente_casos.json"
VERIFICACAO = RAIZ / "data" / "assistente_verificacao.json"
DISTRAITORES = ("via", "sms", "limpeza", "energia", "poco", "retorno")


def metrica_recuperacao(casos: list[dict]) -> list[dict]:
    positivos = [c for c in casos if c["esperado"]]
    metricas = []
    for estrategia, metodo, k in (
        ("secoes", "bm25", 1), ("secoes", "bm25", 2), ("secoes", "bm25", 3),
        ("secoes", "sobreposicao", 3), ("janela48", "bm25", 3), ("janela72", "bm25", 3),
    ):
        linhas = []
        for c in positivos:
            entrada = AssistenteEntrada(pergunta=c["pergunta"], historico=c.get("historico", []))
            consulta = assistente._contextualizar(assistente._anonimizar(entrada.pergunta), entrada.historico)
            consulta = assistente.MARCADORES.sub("", consulta)
            busca = indice(estrategia).buscar(consulta, k=k, metodo=metodo)
            posicao = next((i for i, r in enumerate(busca, 1) if c["esperado"] in r.trecho.evidencias), None)
            linhas.append({"id": c["id"], "posto": posicao, "alvo": c["esperado"],
                           "recuperados": [asdict(r) for r in busca]})
        metricas.append({
            "estrategia": estrategia, "metodo": metodo, "k": k,
            "total_trechos": len(ingerir(estrategia)), "n": len(linhas),
            "hits": sum(linha["posto"] is not None for linha in linhas),
            "hit_rate": sum(linha["posto"] is not None for linha in linhas) / len(linhas),
            "mrr": statistics.mean(1 / linha["posto"] if linha["posto"] else 0 for linha in linhas),
            "casos": linhas,
        })
    return metricas


def julgar(caso: dict, resp: dict, consulta: str) -> dict:
    esperado = caso["esperado"]
    fonte = resp["fontes"][0] if resp["fontes"] else None
    acerto = bool(
        (esperado is not None and fonte and fonte["doc_id"] == esperado and not resp["abstencao"])
        or (esperado is None and resp["abstencao"] and not fonte
            and ("motivo" not in caso or resp["motivo"] == caso["motivo"]))
    )
    trecho = next((t for t in ingerir() if fonte and t.id == fonte["doc_id"]), None)
    fundamentado = bool(trecho and resp["resposta"] == trecho.texto and
                        fonte["trecho"] == trecho.texto and fonte["url"] == trecho.url)
    privacidade = all(s not in consulta and s not in json.dumps(resp, ensure_ascii=False)
                      for s in caso.get("sinteticos", []))
    pertinente = bool(esperado and trecho and trecho.id == esperado)
    return {"acerto": acerto and privacidade, "criterio": caso["criterio"],
            "texto_sustentado": fundamentado if not resp["abstencao"] else None,
            "sustentada_para_a_pergunta": (fundamentado and pertinente) if not resp["abstencao"] else None,
            "sem_exposicao_dos_sinteticos": privacidade}


def avaliar_api(casos: list[dict]) -> dict:
    linhas = []
    with TestClient(app) as cliente:
        modulos = cliente.get("/modulos").json()
        assert any(m["chave"] == "assistente" and m["integrado"] for m in modulos)
        for caso in casos:
            rastros = []

            def registrar(entrada):
                atendimento = assistente.atender(entrada)
                rastros.append(atendimento)
                return atendimento.saida

            inicio = perf_counter()
            with patch.object(assistente, "perguntar", registrar):
                r = cliente.post(ROTA, json={"pergunta": caso["pergunta"], "historico": caso.get("historico", [])})
            ms = (perf_counter() - inicio) * 1000
            assert r.status_code == 200 and r.json()["disponivel"] and len(rastros) == 1, caso["id"]
            resp, rastro = r.json(), rastros[0]
            linhas.append({
                "id": caso["id"], "tipo": caso["tipo"], "pergunta": resp["pergunta_exibida"],
                "consulta": rastro.consulta, "esperado": caso["esperado"], "http": r.status_code,
                "recuperados": [asdict(r) for r in rastro.recuperados], "llm_contexto_ids": rastro.enviados,
                "llm_proposta": rastro.proposta, "resposta": resp, "ms": round(ms, 1),
                "julgamento": julgar(caso, resp, rastro.consulta),
            })
    emitidas = [c for c in linhas if not c["resposta"]["abstencao"]]
    negativos = [c for c in linhas if c["esperado"] is None]
    positivos = [c for c in linhas if c["esperado"] is not None]
    return {
        "n": len(linhas), "acertos": sum(c["julgamento"]["acerto"] for c in linhas),
        "positivos_n": len(positivos), "positivos_corretos": sum(c["julgamento"]["acerto"] for c in positivos),
        "negativos_n": len(negativos), "negativos_corretos": sum(c["julgamento"]["acerto"] for c in negativos),
        "orientacoes_emitidas": len(emitidas),
        "textos_nao_sustentados": sum(not c["julgamento"]["texto_sustentado"] for c in emitidas),
        "orientacoes_nao_sustentadas_para_a_pergunta":
            sum(not c["julgamento"]["sustentada_para_a_pergunta"] for c in emitidas),
        "latencia_mediana_ms": statistics.median(c["ms"] for c in linhas),
        "latencia_max_ms": max(c["ms"] for c in linhas),
        "modos": {modo: sum(c["resposta"]["modo"] == modo for c in linhas)
                  for modo in sorted({c["resposta"]["modo"] for c in linhas})},
        "casos": linhas,
    }


def avaliar_geracao(casos: list[dict]) -> dict:
    rng = random.Random(42)
    trechos = {t.id: t for t in ingerir()}
    linhas = []
    for caso in casos:
        if caso["tipo"] in {"privacidade", "conversa", "emergência", "ambígua", "adversarial"}:
            continue
        esperado = caso["esperado"]
        alternativas = rng.sample([id_ for id_ in DISTRAITORES if id_ != esperado], 2)
        if esperado:
            alternativas.append(esperado)
            rng.shuffle(alternativas)
        elif caso["id"] in {"Q17", "Q25"}:
            # Negativo difícil. Há uma orientação relacionada, mas ela não informa o dado pedido.
            alternativas[0] = "emergencia" if caso["id"] == "Q17" else "poco"
            alternativas = list(dict.fromkeys(alternativas))
        contexto = [trechos[id_] for id_ in alternativas]
        inicio = perf_counter()
        selecao = generator.selecionar(caso["pergunta"], contexto, exigir_llm=True)
        escolhido = selecao.trecho.id if selecao.trecho else None
        linhas.append({
            "id": caso["id"], "pergunta": caso["pergunta"], "esperado": esperado,
            "contexto": [asdict(t) for t in contexto], "llm_proposta": selecao.proposta,
            "resposta": selecao.trecho.texto if selecao.trecho else None,
            "fonte": selecao.trecho.url if selecao.trecho else None,
            "acerto": escolhido == esperado and selecao.motivo != "saida_rejeitada",
            "criterio": caso["criterio"], "primeiro_trecho_acerta": contexto[0].id == esperado,
            "ms": round((perf_counter() - inicio) * 1000, 1),
        })
    return {
        "n": len(linhas), "acertos": sum(c["acerto"] for c in linhas),
        "baseline_primeiro_trecho_acertos": sum(c["primeiro_trecho_acerta"] for c in linhas),
        "positivos_n": sum(c["esperado"] is not None for c in linhas),
        "positivos_corretos": sum(c["esperado"] is not None and c["acerto"] for c in linhas),
        "negativos_n": sum(c["esperado"] is None for c in linhas),
        "negativos_corretos": sum(c["esperado"] is None and c["acerto"] for c in linhas),
        "latencia_mediana_ms": statistics.median(c["ms"] for c in linhas),
        "casos": linhas,
    }


def identificar_modelo() -> dict:
    endereco = generator.endereco_local(os.environ["ASSISTENTE_LLM_URL"])
    url = endereco._replace(path="/v1/models", query="", fragment="").geturl()
    with requests.Session() as sessao:
        sessao.trust_env = False
        resposta = sessao.get(url, timeout=(1, 5), allow_redirects=False)
        if resposta.status_code != 200:
            raise RuntimeError("O servidor não informou o modelo carregado.")
        dados = resposta.json()["data"][0]
    # O servidor pode identificar o modelo pelo caminho local. Registre só o nome do arquivo.
    arquivo = dados["id"].replace("\\", "/").rsplit("/", 1)[-1]
    nomes = {
        "qwen2.5-1.5b-instruct-q4_k_m.gguf": generator.MODELO,
        "qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf": "Qwen2.5-7B-Instruct-Q4_K_M",
    }
    return {"nome": nomes.get(arquivo, arquivo), "arquivo": arquivo,
            "parametros_modelo": dados.get("meta", {}).get("n_params")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--sem-llm", action="store_true", help="Executa recuperação e o fluxo em modo extrativo.")
    args = parser.parse_args()
    casos = json.loads(CASOS.read_text(encoding="utf-8"))
    modelo = identificar_modelo() if not args.sem_llm else None
    resultado = {
        "executado_em": datetime.now().astimezone().isoformat(timespec="seconds"),
        "python": platform.python_version(), "sistema": platform.platform(),
        "modelo": modelo["nome"] if modelo else None,
        "servidor_modelo": modelo,
        "parametros": generator.PARAMETROS if not args.sem_llm else None,
        "prompt": generator.PROMPT if not args.sem_llm else None,
        "recuperacao": metrica_recuperacao(casos),
    }
    if not args.sem_llm:
        resultado["gerador_contexto_controlado"] = avaliar_geracao(casos)
        resultado["api_com_llm"] = avaliar_api(casos)
        resultado["verificacao_com_llm"] = avaliar_api(json.loads(VERIFICACAO.read_text(encoding="utf-8")))
        if not resultado["api_com_llm"]["modos"].get("llm"):
            raise RuntimeError("O fluxo API não executou com LLM.")
        if any("extrativo" in resultado[chave]["modos"]
               for chave in ("api_com_llm", "verificacao_com_llm")):
            raise RuntimeError("O LLM caiu durante a medição integrada.")
    with patch.dict(os.environ, {"ASSISTENTE_LLM_URL": ""}):
        resultado["api_sem_llm"] = avaliar_api(casos)
        resultado["verificacao_sem_llm"] = avaliar_api(json.loads(VERIFICACAO.read_text(encoding="utf-8")))
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Avaliação concluída. Registro: {args.saida}")


if __name__ == "__main__":
    main()
