"""Regressão do módulo com o checkpoint entregue e imagens reservadas."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modulos import impl_visao

FOTOS = Path(__file__).resolve().parents[2] / "entregas_externas/visao/demonstracao/imagens"
pytestmark = pytest.mark.skipif(
    not impl_visao.disponivel(), reason="Instale os pesos e as dependências opcionais de Visão.",
)


def _analisar(cliente, nome, conteudo):
    resposta = cliente.post("/modulos/visao/analisar", files={"imagem": (nome, conteudo, "image/jpeg")})
    assert resposta.status_code == 200
    return resposta.json()


def test_modelo_real_positivo_e_sem_deteccao():
    cliente = TestClient(app)
    nomes = ('India_008389.jpg', 'India_000145.jpg')
    positivo, negativo = [_analisar(cliente, nome, (FOTOS / nome).read_bytes()) for nome in nomes]
    assert positivo["disponivel"] and positivo["tipo_dano"] == "Buraco na pavimentação"
    assert 0 < positivo["confianca"] < 1 and positivo["caixas"] and positivo["latencia_ms"] > 0
    for caixa in positivo["caixas"]:
        assert 0 <= caixa["x"] < 720 and 0 <= caixa["y"] < 720
        assert 0 < caixa["largura"] <= 720 and 0 < caixa["altura"] <= 720
    assert negativo["disponivel"] and negativo["caixas"] == [] and negativo["confianca"] is None


def test_imagem_invalida_nao_derruba_api():
    cliente = TestClient(app)
    saida = _analisar(cliente, "invalido.jpg", b"arquivo de teste")
    assert saida["disponivel"] is False and "ler a imagem" in saida["mensagem"]
    assert cliente.get("/health").json() == {"status": "ok"}
