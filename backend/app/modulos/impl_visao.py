"""Detector de buracos D40 para triagem de possíveis vistorias."""
import io
import hashlib
from importlib.util import find_spec
import json
import os
import threading
import time
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

PASTA = Path(__file__).with_name("pesos_visao")
PESOS = Path(os.environ.get("CAMPOCONECTA_VISAO_PESOS", PASTA / "best.pt"))
AJUSTES = Path(os.environ.get("CAMPOCONECTA_VISAO_AJUSTES", PASTA / "ajustes.json"))
LIMITE_BYTES = 12 * 1024 * 1024
LIMITE_PIXELS = 24_000_000
CLASSE = "Buraco na pavimentação"
TRAVA = threading.Lock()


def disponivel():
    return (PESOS.is_file() and AJUSTES.is_file()
            and find_spec("torch") is not None and find_spec("ultralytics") is not None)


@lru_cache(maxsize=1)
def _carregar():
    import torch
    from ultralytics import YOLO

    torch.set_num_threads(min(4, torch.get_num_threads()))
    esperado = "2e0464c17a6f76349e03389d0e0739623945ef4c81ffcf4ba84c1ae4d072ba62"
    if hashlib.sha256(PESOS.read_bytes()).hexdigest() != esperado:
        raise RuntimeError("Os pesos ativos não correspondem ao YOLO11s auditado. Confira best.pt antes de continuar.")
    ajustes = json.loads(AJUSTES.read_text(encoding="utf-8"))
    if (ajustes.get("imgsz"), ajustes.get("conf"), ajustes.get("nms_iou")) != (640, 0.25, 0.6):
        raise RuntimeError("Ajustes diferentes do ponto operacional auditado: use 640, 0.25 e 0.60.")
    modelo = YOLO(str(PESOS), task="detect")
    if set(modelo.names) != {0}:
        raise RuntimeError("O detector deve conter somente a classe treinada de buraco D40.")
    return modelo, ajustes


def analisar(imagem_bytes: bytes) -> dict:
    inicio = time.perf_counter()
    if not disponivel():
        return {"disponivel": False, "mensagem": "Os pesos avaliados ainda não foram instalados."}
    if not imagem_bytes or len(imagem_bytes) > LIMITE_BYTES:
        return {"disponivel": False, "mensagem": "Selecione uma imagem de até 12 MB."}
    try:
        with Image.open(io.BytesIO(imagem_bytes)) as origem:
            if origem.format not in {"JPEG", "PNG"} or origem.width * origem.height > LIMITE_PIXELS:
                return {"disponivel": False, "mensagem": "Use JPG ou PNG de até 24 megapixels."}
            imagem = ImageOps.exif_transpose(origem).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        return {"disponivel": False, "mensagem": "Não foi possível ler a imagem enviada."}

    with TRAVA:
        modelo, ajustes = _carregar()
        resultado = modelo.predict(
            imagem, imgsz=ajustes["imgsz"], conf=ajustes["conf"],
            iou=ajustes["nms_iou"], device="cpu", max_det=50, verbose=False,
        )[0]
        caixas = []
        for coordenadas, confianca in zip(resultado.boxes.xyxy.tolist(), resultado.boxes.conf.tolist()):
            x1, y1, x2, y2 = coordenadas
            caixas.append({
                "classe": CLASSE, "confianca": round(confianca, 4),
                "x": round(x1, 2), "y": round(y1, 2),
                "largura": round(x2 - x1, 2), "altura": round(y2 - y1, 2),
            })

    return {
        "disponivel": True, "tipo_dano": CLASSE if caixas else None,
        "confianca": max((caixa["confianca"] for caixa in caixas), default=None),
        "caixas": caixas, "latencia_ms": round((time.perf_counter() - inicio) * 1000, 2),
        "mensagem": "Sugestão de vistoria para revisão humana." if caixas else
                    "Nenhum buraco foi sinalizado no limiar atual. A imagem pode não mostrar todo o dano.",
    }
