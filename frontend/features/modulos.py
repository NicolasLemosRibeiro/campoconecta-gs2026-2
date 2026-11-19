"""Painel com as evidências das entregas e o acesso às ferramentas da demonstração."""
import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from providers import api_client
from ui.mensagens import mostrar_erro

RAIZ = Path(__file__).resolve().parents[2]
EVIDENCIAS = RAIZ / "entregas/gs2026.2/evidencias"
CLUSTER = RAIZ / "docs/cluster/resultados"


def _baixar_pdf(rotulo: str, arquivo: str) -> None:
    caminho = EVIDENCIAS / arquivo
    if caminho.is_file():
        st.download_button(rotulo, caminho.read_bytes(), file_name=caminho.name, mime="application/pdf")


def _visao_geral() -> None:
    try:
        modulos = api_client.status_modulos()
    except Exception as erro:
        mostrar_erro(erro)
        return

    linhas = [
        {"Disciplina": "Front End", "Situação": "Interface do portal"},
        {"Disciplina": "RPA", "Situação": "Fluxo integrado ao painel do gestor"},
    ]
    for modulo in modulos:
        if modulo["tipo"] == "endpoint":
            situacao = "Disponível na API" if modulo["integrado"] else "Indisponível na API"
        elif modulo["chave"] == "corpus" and os.getenv("PLN_URL"):
            situacao = "Ferramenta acessível pelo portal"
        elif modulo.get("evidencia_disponivel"):
            situacao = "Artefatos disponíveis"
        else:
            situacao = "Evidência local indisponível"
        linhas.append({"Disciplina": modulo["materia"], "Situação": situacao})
    st.dataframe(linhas, hide_index=True, width="stretch")


def _pln() -> None:
    st.write("A Fábrica de Corpus transforma as fontes em texto, perguntas e respostas, diálogos e um conjunto reservado de teste. O assistente de chuvas usa sua própria base.")
    url = os.getenv("PLN_URL")
    if url:
        st.link_button("Abrir Fábrica de Corpus", url)
    else:
        st.info("Use o iniciador da demonstração para abrir a Fábrica de Corpus.")


def _cluster() -> None:
    arquivos = [CLUSTER / f"{n}_workers" / "resultado.json" for n in (2, 4)]
    if not all(f.is_file() for f in arquivos):
        st.info("Os resultados estão em docs/cluster no repositório.")
        return
    resultados = [json.loads(f.read_text(encoding="utf-8")) for f in arquivos]
    st.caption("Simulação iSPD com 500 tarefas sintéticas de 136 MFlops. Os tempos são simulados.")
    colunas = st.columns(2)
    for coluna, dados in zip(colunas, resultados):
        n = dados["workers"]
        coluna.metric(f"{n} workers", f'{dados["total_simulated_time_s"]:.4f}'.replace(".", ",") + " s")
        captura = CLUSTER / f"{n}_workers" / "captura_results_nativa.png"
        if captura.is_file():
            coluna.image(str(captura), caption=f"Resultado original do iSPD com {n} workers")


def _quantica() -> None:
    st.write("O roadmap propõe medir a espera e testar alocação clássica antes de avaliar uma alternativa híbrida. O benchmark entregue é clássico e usa visitas sintéticas.")
    arquivo = EVIDENCIAS / "quantica_benchmark.csv"
    if arquivo.is_file():
        dados = pd.read_csv(arquivo)
        colunas = {
            "cenario": "Cenário",
            "metodo": "Método",
            "lote": "Visitas por lote",
            "pendentes_media": "Pendentes em média",
            "no_prazo_pct": "No prazo (%)",
        }
        st.dataframe(dados[list(colunas)].rename(columns=colunas), hide_index=True, width="stretch")
    _baixar_pdf("Baixar relatório de Quântica", "quantica_relatorio.pdf")


def _iot() -> None:
    st.write("Sinal à Vista classifica ambiente, fala e sirene no Edge Impulse. O Studio registrou 15 acertos nas gravações reservadas. As tentativas formais ao vivo ficaram sem registro no pacote.")
    url = os.getenv("EDGE_IMPULSE_PROJECT_URL")
    if url:
        st.link_button("Abrir projeto no Edge Impulse", url)
    captura = EVIDENCIAS / "iot_teste_reservado.png"
    if captura.is_file():
        st.image(str(captura), caption="Model testing · captura original do Edge Impulse")
    _baixar_pdf("Baixar relatório de IoT", "iot_relatorio.pdf")


def tela() -> None:
    st.subheader("Módulos do projeto")
    opcoes = {
        "Visão geral": _visao_geral,
        "PLN": _pln,
        "Cluster": _cluster,
        "Quântica": _quantica,
        "IoT": _iot,
    }
    pagina = st.radio("Selecione uma entrega", list(opcoes), horizontal=True)
    opcoes[pagina]()
