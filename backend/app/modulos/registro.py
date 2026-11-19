"""Registro dos módulos das outras matérias.

Como encaixar um módulo de código: criar o arquivo indicado em `arquivo` com a função
`funcao`, respeitando o contrato em schemas/modulos.py. Sem o arquivo, o sistema usa o
stub e continua funcionando. Os artefatos entregues têm sua própria indicação.
"""
import importlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from .. import config

logger = logging.getLogger(__name__)


class ErroIntegracaoVisao(RuntimeError):
    """A implementação existe ou foi configurada, mas não pôde ser carregada."""


@dataclass(frozen=True)
class Slot:
    chave: str
    materia: str
    tipo: str                      # "endpoint" | "arquivos" | "documento"
    contrato: str                  # o que entra e o que sai
    arquivo: Optional[str] = None  # módulo Python esperado (só para endpoint)
    funcao: Optional[str] = None
    pasta: str = ""                # onde o responsável coloca a entrega


SLOTS: list[Slot] = [
    Slot("visao", "Visão Computacional", "endpoint",
         "imagem (bytes) -> VisaoSaida {tipo_dano, confianca, caixas[], latencia_ms}",
         "app.modulos.impl_visao", "analisar", "entregas/gs2026.2/modulos/CampoConecta_YOLO52_Integracao_Auditada_19Nov2026.zip"),
    Slot("assistente", "Generative AI", "endpoint",
         "AssistenteEntrada {pergunta, historico} -> AssistenteSaida {resposta, fontes[], abstencao}",
         "app.modulos.impl_assistente", "perguntar", "entregas/gs2026.2/modulos/GS2026.2_Generative_AI_CampoConecta.zip"),
    Slot("corpus", "PLN (Fábrica de Corpus)", "arquivos",
         "Ferramenta separada, acessível pelo portal na demonstração local",
         pasta="entregas/gs2026.2/modulos/GS_PLN_CitizenTech_Entrega_Professor_19Nov2026.zip"),
    Slot("iot", "IoT (Sinal à Vista)", "documento",
         "Classificador Edge Impulse independente",
         pasta="entregas/gs2026.2/evidencias/iot_relatorio.pdf"),
    Slot("cluster", "Cluster Computing", "documento",
         "Simulação iSPD da triagem em lote",
         pasta="docs/cluster/resultados/2_workers/resultado.json"),
    Slot("quantica", "Computação Quântica", "documento",
         "Roadmap e benchmark clássico",
         pasta="entregas/gs2026.2/evidencias/quantica_relatorio.pdf"),
    Slot("governanca", "Governança em IA e Business Analytics", "documento",
         "Relatório de integração e evidências",
         pasta="entregas/gs2026.2/Relatorio_Governanca_CampoConecta.docx"),
]


def carregar(slot: Slot) -> Optional[Callable]:
    """Visão é obrigatória neste pacote; falhas preservam a exceção original."""
    if slot.tipo != "endpoint" or not slot.arquivo:
        return None
    try:
        modulo = importlib.import_module(slot.arquivo)
        funcao = getattr(modulo, slot.funcao)
        if slot.chave == "visao" and not callable(funcao):
            raise AttributeError(f"{slot.arquivo}.{slot.funcao} não é uma função chamável")
        return funcao
    except (ImportError, AttributeError) as erro:
        if slot.chave == "visao":
            logger.exception("Falha real ao carregar %s.%s", slot.arquivo, slot.funcao)
            raise ErroIntegracaoVisao(
                f"{type(erro).__name__}: {erro}"
            ) from erro
        return None


def _endpoint_disponivel(slot: Slot) -> bool:
    if slot.tipo != "endpoint":
        return False
    try:
        if carregar(slot) is None:
            return False
        verificar = getattr(importlib.import_module(slot.arquivo), "disponivel", None)
        return bool(verificar()) if verificar else True
    except Exception:
        logger.exception("Falha ao verificar %s", slot.chave)
        return False


def status() -> list[dict]:
    return [
        {
            "chave": slot.chave,
            "materia": slot.materia,
            "tipo": slot.tipo,
            "contrato": slot.contrato,
            "pasta": slot.pasta or slot.arquivo,
            "integrado": _endpoint_disponivel(slot),
            "evidencia_disponivel": bool(slot.pasta and (Path(config.RAIZ) / slot.pasta).is_file()),
        }
        for slot in SLOTS
    ]
