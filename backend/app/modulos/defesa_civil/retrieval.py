"""Ingestão da base editorial e índice BM25 em memória."""
import json
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

CORPUS = Path(__file__).with_name("corpus.json")
STOP = set("a o e que eu voce de da do dos das em um uma os as se na no nos nas para por com ao ou me meu minha isso ja posso pode como qual quais quando onde fazer devo tem esta estou ta fica ainda muito foi ser".split())
VARIANTES = {
    "atravesso": "atravessar", "atravesse": "atravessar", "passo": "passar",
    "alagada": "alagamento", "alagado": "alagamento", "alagadas": "alagamento",
    "alagou": "alagamento", "alagamentos": "alagamento", "inundada": "inundacao",
    "inundacoes": "inundacao", "enchentes": "enchente", "enchendo": "subindo",
    "tomadas": "tomada", "alimentos": "alimento", "comidas": "comida",
    "bebida": "beber", "bebo": "beber", "pocos": "poco", "aguas": "agua",
    "calhas": "calha", "ralos": "ralo", "pontes": "ponte", "ruas": "rua",
    "remedios": "remedio", "roupas": "roupa", "lanternas": "lanterna",
    "avisos": "aviso", "alertas": "alerta", "voltamos": "voltar", "volto": "voltar",
    "voltou": "voltar", "cadastra": "cadastrar", "presos": "preso", "presa": "preso",
    "ilhados": "ilhado", "ilhada": "ilhado", "chuvas": "chuva", "feridas": "ferido",
}
GENERICO = set("agua chuva forte casa enchente alagamento inundacao depois antes temporal caminho local risco".split())
TOP_K = 2
LIMIAR = 1.6


def normalizar(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto.casefold())
                   if not unicodedata.combining(c))


def tokens(texto: str) -> list[str]:
    return [VARIANTES.get(palavra, palavra) for palavra in re.findall(r"[a-z0-9]+", normalizar(texto))
            if palavra not in STOP]


@dataclass(frozen=True)
class Trecho:
    id: str
    documento_id: str
    titulo: str
    secao: str
    url: str
    consultado_em: str
    texto: str
    indice: str
    evidencias: tuple[str, ...]


@lru_cache(maxsize=4)
def ingerir(estrategia: str = "secoes") -> tuple[Trecho, ...]:
    base = json.loads(CORPUS.read_text(encoding="utf-8"))
    resultado = []
    for doc in base["documentos"]:
        meta = (doc["id"], doc["titulo"], doc["url"], base["consultado_em"])
        if estrategia == "secoes":
            for secao in doc["secoes"]:
                resultado.append(Trecho(
                    secao["id"], meta[0], meta[1], secao["titulo"], meta[2], meta[3],
                    secao["texto"], f'{secao["titulo"]} {secao["termos"]} {secao["texto"]}',
                    (secao["id"],),
                ))
            continue

        # Janelas sobre o mesmo material indexável, sempre dentro de um documento.
        if estrategia not in {"janela48", "janela72"}:
            raise ValueError("Estratégia de chunking desconhecida")
        tamanho, overlap = (48, 12) if estrategia == "janela48" else (72, 18)
        palavras, intervalos = [], []
        for secao in doc["secoes"]:
            palavras.extend(f'{secao["titulo"]} {secao["termos"]}'.split())
            inicio_texto = len(palavras)
            palavras.extend(secao["texto"].split())
            intervalos.append((secao["id"], inicio_texto, len(palavras)))
        for inicio in range(0, len(palavras), tamanho - overlap):
            fim = min(inicio + tamanho, len(palavras))
            texto = " ".join(palavras[inicio:fim])
            completos = tuple(s for s, a, b in intervalos if inicio <= a and b <= fim)
            resultado.append(Trecho(f"{doc['id']}:{inicio}", meta[0], meta[1],
                                    "Janela de palavras", meta[2], meta[3], texto, texto, completos))
            if fim == len(palavras):
                break
    return tuple(resultado)


@dataclass(frozen=True)
class Resultado:
    trecho: Trecho
    score: float


class Indice:
    def __init__(self, trechos: tuple[Trecho, ...]):
        self.trechos = trechos
        self.frequencias = [Counter(tokens(t.indice)) for t in trechos]
        self.tamanhos = [sum(f.values()) for f in self.frequencias]
        self.media = sum(self.tamanhos) / len(trechos)
        df = Counter(termo for freq in self.frequencias for termo in freq)
        self.idf = {t: math.log(1 + (len(trechos) - n + 0.5) / (n + 0.5))
                    for t, n in df.items()}

    def buscar(self, pergunta: str, k: int = TOP_K, metodo: str = "bm25") -> list[Resultado]:
        consulta = set(tokens(pergunta))
        resultados = []
        for trecho, freq, tamanho in zip(self.trechos, self.frequencias, self.tamanhos):
            termos = consulta.intersection(freq)
            if metodo == "sobreposicao":
                score = len(termos)
            else:
                k1, b = 1.5, 0.75
                fator = k1 * (1 - b + b * tamanho / self.media)
                score = sum(self.idf[t] * freq[t] * (k1 + 1) / (freq[t] + fator) for t in sorted(termos))
            if score:
                resultados.append(Resultado(trecho, score))
        return sorted(resultados, key=lambda item: -item.score)[:k]


@lru_cache(maxsize=4)
def indice(estrategia: str = "secoes") -> Indice:
    return Indice(ingerir(estrategia))
