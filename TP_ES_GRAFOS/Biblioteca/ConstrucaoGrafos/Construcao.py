"""Construcao.py
================
Fábrica para instanciar e preencher as classes concretas de grafo.

Este módulo usa a API comum definida em AbstractGraph para construir os dois
formatos de armazenamento disponíveis no projeto:
    - AdjacencyListGraph
    - AdjacencyMatrixGraph

A direção das relações vem dos arquivos processados em dados_processados/:
    - de   -> vértice de origem
    - para -> vértice de destino

O mapeamento de usuários para índices é lido do JSON gerado por
MapeamentoVertices.py. Se o arquivo ainda não existir, ele é regenerado.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

CURRENT_DIR = Path(__file__).resolve().parent
ESTRUTURA_DIR = CURRENT_DIR.parent / "EstruturadeClasses"
EXTRACAO_DIR = CURRENT_DIR.parent / "ExtracaoDados"

sys.path.insert(0, str(CURRENT_DIR))
sys.path.insert(0, str(ESTRUTURA_DIR))

from AbstractGraph import AbstractGraph
from AdjacencyListGraph import AdjacencyListGraph
from AdjacencyMatrixGraph import AdjacencyMatrixGraph
from MapeamentoVertices import gerar_mapeamento_vertices


class Construcao:
    """Constroi grafos concretos a partir dos dados processados."""

    def __init__(self, dados_processados: Path | None = None, arquivo_mapeamento: Path | None = None) -> None:
        self.dados_processados = Path(dados_processados) if dados_processados else EXTRACAO_DIR / "dados_processados"
        self.arquivo_mapeamento = Path(arquivo_mapeamento) if arquivo_mapeamento else CURRENT_DIR / "mapeamento_vertices.json"
        self._mapeamento_cache: Dict[str, int] | None = None

    def construir_lista(self) -> AdjacencyListGraph:
        """Cria e preenche um grafo usando lista de adjacência."""
        grafo = AdjacencyListGraph(self._quantidade_vertices())
        self._preencher_grafo(grafo)
        return grafo

    def construir_matriz(self) -> AdjacencyMatrixGraph:
        """Cria e preenche um grafo usando matriz de adjacência."""
        grafo = AdjacencyMatrixGraph(self._quantidade_vertices())
        self._preencher_grafo(grafo)
        return grafo

    def construir_todos(self) -> Tuple[AdjacencyListGraph, AdjacencyMatrixGraph]:
        """Cria os dois grafos concretos com a mesma base de dados."""
        return self.construir_lista(), self.construir_matriz()

    def _carregar_mapeamento(self) -> Dict[str, int]:
        """Carrega o mapa global nome -> índice, gerando-o se necessário."""
        if self._mapeamento_cache is not None:
            return self._mapeamento_cache

        if self.arquivo_mapeamento.exists():
            with self.arquivo_mapeamento.open("r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)

            if isinstance(dados, dict) and "global" in dados:
                mapeamento = dados["global"]["mapeamento"]
            else:
                mapeamento = dados
        else:
            dados = gerar_mapeamento_vertices(self.dados_processados, self.arquivo_mapeamento)
            mapeamento = dados["global"]["mapeamento"]

        self._mapeamento_cache = {str(chave): int(valor) for chave, valor in mapeamento.items()}
        return self._mapeamento_cache

    def _quantidade_vertices(self) -> int:
        """Retorna a quantidade de vertices necessária para os grafos."""
        return len(self._carregar_mapeamento())

    def _preencher_grafo(self, grafo: AbstractGraph) -> None:
        """Aplica os rótulos dos vértices e insere as arestas direcionais."""
        mapeamento = self._carregar_mapeamento()

        for usuario, indice in mapeamento.items():
            grafo.setVertexLabel(indice, usuario)

        for interacao in self._carregar_interacoes():
            origem_nome = interacao.get("de")
            destino_nome = interacao.get("para")
            peso = interacao.get("peso", 0)

            if not isinstance(origem_nome, str) or not isinstance(destino_nome, str):
                continue

            if origem_nome not in mapeamento or destino_nome not in mapeamento:
                continue

            origem = mapeamento[origem_nome]
            destino = mapeamento[destino_nome]

            if grafo.hasEdge(origem, destino):
                peso_atual = grafo.getEdgeWeight(origem, destino)
                grafo.setEdgeWeight(origem, destino, peso_atual + float(peso))
            else:
                grafo.setEdgeWeight(origem, destino, float(peso))

    def _carregar_interacoes(self) -> Iterable[Dict[str, object]]:
        """Lê todos os JSONs processados e devolve as interações brutas."""
        nomes = ["comentarios.json", "fechamentos.json", "reviews_merges.json"]

        for nome in nomes:
            arquivo = self.dados_processados / nome
            if not arquivo.exists():
                continue

            with arquivo.open("r", encoding="utf-8") as entrada:
                dados = json.load(entrada)

            if isinstance(dados, list):
                for item in dados:
                    if isinstance(item, dict):
                        yield item

            elif isinstance(dados, dict):
                for chave in ("nodes", "items"):
                    itens = dados.get(chave)
                    if isinstance(itens, list):
                        for item in itens:
                            if isinstance(item, dict):
                                yield item
                        break
                else:
                    yield dados


if __name__ == "__main__":
    construtor = Construcao()
    grafo_lista, grafo_matriz = construtor.construir_todos()

    print(f"Grafo em lista: {grafo_lista.getVertexCount()} vertices, {grafo_lista.getEdgeCount()} arestas")
    print(f"Grafo em matriz: {grafo_matriz.getVertexCount()} vertices, {grafo_matriz.getEdgeCount()} arestas")
