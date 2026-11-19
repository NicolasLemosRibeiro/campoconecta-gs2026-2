"""Diagnóstico executável: revela importação e faz inferência real, sem enviar dados externos."""
from pathlib import Path
import sys, json, hashlib, importlib, importlib.metadata, traceback, argparse
ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / "backend"))
    importlib.invalidate_caches()
    esperado = "2e0464c17a6f76349e03389d0e0739623945ef4c81ffcf4ba84c1ae4d072ba62"
    print(f"Python da conferência: {sys.executable}", flush=True)
    from app.modulos import registro, impl_visao
    print(f"Implementação importada: {impl_visao.__file__}", flush=True)
    assert Path(impl_visao.__file__).resolve() == (ROOT/"backend/app/modulos/impl_visao.py").resolve(), "Outro projeto está sendo importado."
    funcao = registro.carregar(next(s for s in registro.SLOTS if s.chave == "visao"))
    assert callable(funcao), "A função analisar não está disponível no módulo importado."
    assert impl_visao.disponivel(), "Pesos, ajustes, Torch ou Ultralytics ausentes neste ambiente."
    hash_pesos = hashlib.sha256(impl_visao.PESOS.read_bytes()).hexdigest()
    assert hash_pesos == esperado, "Pesos diferentes da versão auditada."
    foto=ROOT/"entregas_externas/visao/demonstracao/imagens/India_008389.jpg"
    from app.schemas.modulos import VisaoSaida
    positivo = VisaoSaida.model_validate(funcao(foto.read_bytes()))
    assert positivo.disponivel and positivo.caixas and positivo.latencia_ms > 0, positivo
    with __import__("PIL.Image",fromlist=["Image"]).open(foto) as imagem:
        w,h=imagem.size
    for caixa in positivo.caixas:
        assert 0 <= caixa.x < w and 0 <= caixa.y < h
        assert caixa.largura > 0 and caixa.altura > 0 and caixa.x+caixa.largura <= w+0.02 and caixa.y+caixa.altura <= h+0.02
        assert .25 <= caixa.confianca <= 1
    resultado={"status":"aprovado", "python":sys.executable,"plataforma":sys.platform,"implementacao":str(Path(impl_visao.__file__).resolve()),"sha256_pesos":hash_pesos,
       "ajustes":json.loads(impl_visao.AJUSTES.read_text()),"versoes":{n:importlib.metadata.version(n) for n in ["numpy","opencv-python","ultralytics","torch","pyarrow"]},"inferencia_real":positivo.model_dump()}
    if args.saida:
        args.saida.parent.mkdir(parents=True,exist_ok=True)
        args.saida.write_text(json.dumps(resultado,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(resultado,ensure_ascii=False,indent=2),flush=True)
    print("YOLO CARREGADO E INFERÊNCIA REAL APROVADA.",flush=True)

if __name__ == "__main__":
    try:main()
    except Exception:
        traceback.print_exc()
        print("DIAGNÓSTICO REPROVADO: o erro original está acima. Não trate o módulo como integrado.",file=sys.stderr)
        sys.exit(1)
