"""Contratos dos módulos que outras matérias podem encaixar.

Quem for entregar um módulo só precisa respeitar estas entradas e saídas.
"""
from typing import Annotated, Optional

from pydantic import BaseModel, Field, StringConstraints


class Caixa(BaseModel):
    classe: str
    confianca: float = Field(ge=0, le=1)
    x: float
    y: float
    largura: float
    altura: float


class VisaoSaida(BaseModel):
    disponivel: bool = True
    tipo_dano: Optional[str] = None
    confianca: Optional[float] = Field(default=None, ge=0, le=1)
    caixas: list[Caixa] = []
    latencia_ms: Optional[float] = None
    mensagem: Optional[str] = None


class AssistenteEntrada(BaseModel):
    pergunta: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]
    historico: list[dict] = Field(default_factory=list, max_length=8)


class Fonte(BaseModel):
    doc_id: Optional[str] = None
    titulo: str
    trecho: str
    url: Optional[str] = None
    secao: Optional[str] = None
    consultado_em: Optional[str] = None


class AssistenteSaida(BaseModel):
    disponivel: bool = True
    resposta: Optional[str] = None
    fontes: list[Fonte] = []
    abstencao: bool = False
    mensagem: Optional[str] = None
    modo: Optional[str] = None
    motivo: Optional[str] = None
    pergunta_exibida: Optional[str] = None
