"""Inicia API, interface CampoConecta e Fábrica de Corpus com dados de demonstração."""
import argparse
import json
import os
from hashlib import file_digest
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
from urllib.error import URLError
from urllib.request import urlopen
import webbrowser
from zipfile import ZipFile

RAIZ = Path(__file__).resolve().parent
ATIVOS = RAIZ / "entregas/gs2026.2"
PACOTE_PLN = ATIVOS / "modulos/GS_PLN_CitizenTech_Entrega_Professor_19Nov2026.zip"
ESTADO = RAIZ / ".demonstracao"
AMBIENTE = ESTADO / "ambiente"
FORNECEDOR_TORCH = "https://download.pytorch.org/whl/cpu"


def preparar_pln() -> Path:
    manifesto = json.loads((ATIVOS / "Verificacoes_Governanca.json").read_text(encoding="utf-8"))
    esperado = manifesto["arquivos_originais"][PACOTE_PLN.name]["sha256"]
    with PACOTE_PLN.open("rb") as arquivo:
        if file_digest(arquivo, "sha256").hexdigest() != esperado:
            raise RuntimeError("ZIP de PLN diferente do original. Confira o arquivo em entregas/gs2026.2/modulos/.")
    destino = ESTADO / f"pln-{esperado[:12]}"
    if not (destino / "app.py").is_file():
        with tempfile.TemporaryDirectory(dir=ESTADO) as temporario, ZipFile(PACOTE_PLN) as pacote:
            pasta = Path(temporario)
            pacote.extractall(pasta)
            (pasta / "corpus_citizentech 2").replace(destino)
    return destino


def preparar_python(pln: Path) -> Path:
    uv = shutil.which("uv")
    if not uv:
        raise RuntimeError("Instale o uv pelo site oficial (docs.astral.sh/uv) e abra um novo terminal.")
    requisitos = [
        RAIZ / "backend/requirements.txt",
        RAIZ / "frontend/requirements.txt",
        RAIZ / "requirements-integrado.txt",
        pln / "requirements.txt",
    ]
    assinatura = "|".join(os.linesep.join(f.read_text().splitlines()) for f in requisitos)
    marcador = AMBIENTE / "requisitos-demonstracao.txt"
    exe = AMBIENTE / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not exe.is_file():
        subprocess.run([uv, "venv", "--python", "3.12", str(AMBIENTE)], check=True)
    if not marcador.is_file() or marcador.read_text() != assinatura:
        pip = [uv, "pip", "install", "--python", str(exe)]
        subprocess.run([*pip, "--index", FORNECEDOR_TORCH, "torch==2.7.1", "torchvision==0.22.1"], check=True)
        subprocess.run([*pip, *(arg for req in requisitos for arg in ("-r", str(req)))], check=True)
        marcador.write_text(assinatura)
    return exe


def esperar(url: str, processo: subprocess.Popen, limite: int = 60) -> None:
    fim = time.monotonic() + limite
    while time.monotonic() < fim and processo.poll() is None:
        try:
            with urlopen(url, timeout=1) as resposta:
                if resposta.status == 200:
                    return
        except (URLError, TimeoutError):
            time.sleep(0.3)
    raise RuntimeError(f"Serviço indisponível em {url}. Confira os logs em {ESTADO}.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--porta-api", type=int, default=8000)
    parser.add_argument("--porta-web", type=int, default=8501)
    parser.add_argument("--porta-pln", type=int, default=8502)
    parser.add_argument("--sem-abrir", action="store_true")
    parser.add_argument("--com-modelo", action="store_true",
                        help="Usa o llama.cpp original, previamente iniciado em 127.0.0.1:8088.")
    args = parser.parse_args()
    portas = [args.porta_api, args.porta_web, args.porta_pln]
    if len(set(portas)) != len(portas) or any(not 1 <= porta <= 65535 for porta in portas):
        parser.error("Escolha três portas distintas, entre 1 e 65535.")
    for porta in portas:
        with socket.socket() as teste:
            try:
                teste.bind(("127.0.0.1", porta))
            except OSError:
                parser.error(f"A porta {porta} está em uso. Escolha outra pelos argumentos de porta.")

    ESTADO.mkdir(exist_ok=True)
    pln = preparar_pln()
    python = preparar_python(pln)
    base_api, web, corpus = [f"http://127.0.0.1:{porta}" for porta in portas]
    modelo = ""
    if args.com_modelo:
        try:
            with urlopen("http://127.0.0.1:8088/health", timeout=4):
                modelo = "http://127.0.0.1:8088/v1/chat/completions"
        except (URLError, TimeoutError):
            parser.error("Inicie o servidor local de Generative AI na porta 8088 e tente novamente.")

    env = os.environ | {
        "API_URL": base_api, "API_TIMEOUT_S": "90", "PLN_URL": corpus,
        "ASSISTENTE_LLM_URL": modelo, "GEMINI_API_KEY": "", "GEMINI_MODEL": "",
        "SMTP_HOST": "", "EMAIL_ORIGEM": "campoconecta@exemplo.invalid",
        "EMAIL_DESTINO": "extensao.rural@exemplo.invalid", "GESTOR_PIN": "",
        "DB_PATH": str(ESTADO / "relatos.db"), "OUTBOX_DIR": str(ESTADO / "outbox"),
        "LOG_PATH": str(ESTADO / "robo.log"), "CACHE_CEP_PATH": str(ESTADO / "cep.json"),
        "YOLO_CONFIG_DIR": str(ESTADO / "yolo"),
        "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
    }
    processos = []

    def executar(nome, cwd, comandos):
        with (ESTADO / f"{nome}.log").open("wb") as log:
            processo = subprocess.Popen([str(python), "-X", "utf8", *comandos], cwd=cwd,
                                       stdout=log, stderr=subprocess.STDOUT, env=env)
        processos.append(processo)
        return processo

    def streamlit(porta, arquivo):
        return ["-m", "streamlit", "run", str(arquivo), "--server.address", "127.0.0.1",
                "--server.port", str(porta), "--server.headless", "true"]

    try:
        api = executar("api", ESTADO, ["-m", "uvicorn", "--app-dir", str(RAIZ / "backend"),
                                      "app.main:app", "--host", "127.0.0.1", "--port", str(args.porta_api)])
        interface = executar("interface", RAIZ / "frontend", streamlit(args.porta_web, RAIZ / "frontend/app.py"))
        fabrica = executar("pln", pln, streamlit(args.porta_pln, pln / "app.py"))
        for url, processo in [(base_api + "/health", api), (web, interface), (corpus, fabrica)]:
            esperar(url, processo)
        print(f"CampoConecta pronto: {web}\nFábrica de Corpus: {corpus}\nCtrl+C encerra a demonstração.", flush=True)
        if not args.sem_abrir:
            webbrowser.open(web)
        while all(p.poll() is None for p in processos):
            time.sleep(0.5)
        raise RuntimeError(f"Um serviço encerrou. Confira os logs em {ESTADO}.")
    except KeyboardInterrupt:
        print("\nDemonstração encerrada.")
    finally:
        for p in reversed(processos):
            if p.poll() is None:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    p.terminate()
        for p in processos:
            p.wait()


if __name__ == "__main__":
    main()
