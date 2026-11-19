"""Regressões: falhas de importação devem ser diagnosticáveis, nunca sucesso falso."""
from types import ModuleType
import sys
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.modulos import registro

SLOT=next(s for s in registro.SLOTS if s.chave=='visao')

def test_funcao_ausente_preserva_causa_e_api_continua(monkeypatch,caplog):
    monkeypatch.setitem(sys.modules,SLOT.arquivo,ModuleType(SLOT.arquivo))
    with pytest.raises(registro.ErroIntegracaoVisao) as exc:
        registro.carregar(SLOT)
    assert isinstance(exc.value.__cause__,AttributeError)
    cliente=TestClient(app)
    resposta=cliente.post('/modulos/visao/analisar',files={'imagem':('teste.jpg',b'x','image/jpeg')})
    assert resposta.status_code==200 and not resposta.json()['disponivel']
    assert 'diagnosticar_visao.py' in resposta.json()['mensagem']
    estado=cliente.get('/modulos')
    assert estado.status_code==200 and not next(x for x in estado.json() if x['chave']=='visao')['integrado']
    assert 'AttributeError' in caplog.text
    assert cliente.get('/health').status_code==200

def test_dependencia_ausente_nao_vira_modulo_pendente(monkeypatch):
    importar=registro.importlib.import_module
    def quebra(nome):
        if nome==SLOT.arquivo:raise ModuleNotFoundError("No module named 'PIL'",name='PIL')
        return importar(nome)
    monkeypatch.setattr(registro.importlib,'import_module',quebra)
    with pytest.raises(registro.ErroIntegracaoVisao) as exc:registro.carregar(SLOT)
    assert isinstance(exc.value.__cause__,ModuleNotFoundError) and 'PIL' in str(exc.value)

def test_atributo_nao_chamavel_reprovado(monkeypatch):
    modulo=ModuleType(SLOT.arquivo);modulo.analisar=None
    monkeypatch.setitem(sys.modules,SLOT.arquivo,modulo)
    with pytest.raises(registro.ErroIntegracaoVisao):registro.carregar(SLOT)

def test_modulos_opcionais_preservam_comportamento(monkeypatch):
    slot=next(s for s in registro.SLOTS if s.chave=='assistente')
    monkeypatch.setitem(sys.modules,slot.arquivo,ModuleType(slot.arquivo))
    assert registro.carregar(slot) is None
