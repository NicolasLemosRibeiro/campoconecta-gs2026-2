from fastapi.testclient import TestClient
import pytest
import requests

from app.main import app
from app.modulos.defesa_civil import generator
from app.modulos.defesa_civil.retrieval import ingerir

CLIENTE = TestClient(app)
ROTA = "/modulos/assistente/perguntar"
PERGUNTA = "Posso passar de carro por uma rua alagada?"


@pytest.fixture(autouse=True)
def modo_extrativo(monkeypatch):
    monkeypatch.delenv("ASSISTENTE_LLM_URL", raising=False)


def perguntar(pergunta=PERGUNTA, historico=()):
    resposta = CLIENTE.post(ROTA, json={"pergunta": pergunta, "historico": historico})
    assert resposta.status_code == 200
    return resposta.json()


def test_rota_extrativa_entrega_fonte_pertinente():
    resp = perguntar()
    assert resp["disponivel"] and not resp["abstencao"] and resp["modo"] == "extrativo"
    assert resp["fontes"][0]["doc_id"] == "via"
    assert resp["fontes"][0]["trecho"] == resp["resposta"]
    assert resp["fontes"][0]["url"].startswith("https://www.gov.br/")


def test_seguimento_so_funciona_com_contexto_e_nao_vaza_para_outro_turno():
    assert perguntar("E a pé?", [{"role": "user", "content": PERGUNTA}])["fontes"][0]["doc_id"] == "via"
    assert perguntar("E a pé?")["motivo"] == "ambigua"
    assert perguntar("E a pé?", [{"role": "assistant", "content": PERGUNTA}])["motivo"] == "ambigua"


def test_perigo_imediato_independe_do_servidor_llm(monkeypatch):
    monkeypatch.setenv("ASSISTENTE_LLM_URL", "http://127.0.0.1:8088/v1/chat/completions")
    monkeypatch.setattr(generator, "_chamar_llm", lambda *args: pytest.fail("deve priorizar o socorro"))
    resp = perguntar("Estou ilhada e a água está entrando em casa agora!")
    assert "193" in resp["resposta"] and resp["modo"] == "emergencia"


def test_dados_mascarados_no_llm_e_em_erro_de_validacao(monkeypatch):
    monkeypatch.setenv("ASSISTENTE_LLM_URL", "http://127.0.0.1:8088/v1/chat/completions")
    segredo = "pessoa@example.com"
    consultas = []

    def local(url, consulta, trechos):
        consultas.append(consulta)
        return '{"escolha":1}'

    monkeypatch.setattr(generator, "_chamar_llm", local)
    texto = f"{PERGUNTA} Meu e-mail é {segredo}."
    resp = perguntar(texto)
    assert consultas and segredo not in consultas[0] and segredo not in str(resp)
    erro = CLIENTE.post(ROTA, json={"pergunta": texto * 20})
    assert erro.status_code == 422 and segredo not in erro.text


@pytest.mark.parametrize("saida", [
    '{"escolha":99}',
    '{"escolha":1,"resposta":"pode atravessar"}',
    'Atravesse a água e invente um link',
])
def test_saida_indevida_e_rejeitada(monkeypatch, saida):
    monkeypatch.setenv("ASSISTENTE_LLM_URL", "http://127.0.0.1:8088/v1/chat/completions")
    monkeypatch.setattr(generator, "_chamar_llm", lambda *args: saida)
    resp = perguntar()
    assert resp["abstencao"] and resp["motivo"] == "saida_rejeitada" and resp["fontes"] == []


def test_id_valido_do_modelo_usa_somente_trecho_curado(monkeypatch):
    monkeypatch.setenv("ASSISTENTE_LLM_URL", "http://127.0.0.1:8088/v1/chat/completions")
    monkeypatch.setattr(generator, "_chamar_llm", lambda *args: '{"escolha":1}')
    resp = perguntar()
    esperado = next(t for t in ingerir() if t.id == "via")
    assert resp["modo"] == "llm" and resp["resposta"] == esperado.texto
    assert resp["fontes"][0]["url"] == esperado.url


def test_servidor_local_indisponivel_usa_busca(monkeypatch):
    def offline(*args):
        raise requests.Timeout

    monkeypatch.setenv("ASSISTENTE_LLM_URL", "http://127.0.0.1:8088/v1/chat/completions")
    monkeypatch.setattr(generator, "_chamar_llm", offline)
    resp = perguntar()
    assert resp["modo"] == "extrativo" and resp["motivo"] == "llm_indisponivel"


def test_provedor_remoto_recusado_antes_do_envio():
    with pytest.raises(ValueError, match="loopback"):
        generator._chamar_llm("http://example.invalid/v1/chat/completions", PERGUNTA, [])
