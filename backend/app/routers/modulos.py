"""Endpoints dos módulos abertos. Sem módulo real, devolvem o stub (disponivel=false)."""
import logging
import time

from fastapi import APIRouter, File, UploadFile
from starlette.concurrency import run_in_threadpool

from ..modulos import registro
from ..schemas.modulos import AssistenteEntrada, AssistenteSaida, VisaoSaida

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/modulos", tags=["modulos"])
_SLOTS = {s.chave: s for s in registro.SLOTS}


@router.get("")
def listar_modulos():
    return registro.status()


@router.post("/visao/analisar", response_model=VisaoSaida)
async def analisar_imagem(imagem: UploadFile = File(...)):
    try:
        func = registro.carregar(_SLOTS["visao"])
    except registro.ErroIntegracaoVisao:
        logger.exception("Falha de integração do YOLO; execute diagnosticar_visao.py com o Python da API")
        return VisaoSaida(disponivel=False, mensagem=(
            "Não foi possível carregar a implementação do YOLO. "
            "Execute diagnosticar_visao.py com o mesmo Python da API; o erro original está no terminal do backend."
        ))
    if func is None:
        return VisaoSaida(disponivel=False, mensagem="Implementação de Visão ausente ou inválida; execute diagnosticar_visao.py.")
    limite_bytes = 12 * 1024 * 1024
    conteudo = await imagem.read(limite_bytes + 1)
    if len(conteudo) > limite_bytes:
        return VisaoSaida(disponivel=False, mensagem="Selecione uma imagem de até 12 MB.")
    inicio = time.perf_counter()
    try:
        saida = VisaoSaida.model_validate(await run_in_threadpool(func, conteudo))
    except Exception:
        logger.exception("A implementação de Visão falhou ao executar a inferência real")
        return VisaoSaida(disponivel=False, mensagem="O YOLO falhou nesta imagem. Consulte o erro original no terminal da API ou execute diagnosticar_visao.py.")
    if saida.latencia_ms is None:
        saida.latencia_ms = round((time.perf_counter() - inicio) * 1000, 1)
    return saida


@router.post("/assistente/perguntar", response_model=AssistenteSaida)
def perguntar(entrada: AssistenteEntrada):
    func = registro.carregar(_SLOTS["assistente"])
    if func is None:
        return AssistenteSaida(disponivel=False, mensagem="Assistente ainda não integrado.")
    try:
        return AssistenteSaida.model_validate(func(entrada))
    except Exception:
        logger.exception("Falha ao executar o assistente")
        return AssistenteSaida(disponivel=False, mensagem="O assistente falhou nesta pergunta.")
