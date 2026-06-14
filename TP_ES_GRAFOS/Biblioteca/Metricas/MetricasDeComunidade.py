"""Métricas de comunidade para os grafos do projeto.

Este módulo trabalha diretamente com as implementações de grafo já construídas
no projeto, sem uso de bibliotecas prontas como networkx.

Funcionalidades:
- Detecção de comunidades por label propagation em projeção não direcionada
- Cálculo de modularidade da partição encontrada
- Identificação de bridging ties, isto é, vértices que conectam comunidades
  diferentes com frequência relevante

O módulo aceita tanto AdjacencyListGraph quanto AdjacencyMatrixGraph, desde
que exponham a API comum definida em AbstractGraph.
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Set, Tuple

CURRENT_DIR = Path(__file__).resolve().parent
ESTRUTURA_DIR = CURRENT_DIR.parent / "EstruturadeClasses"

sys.path.insert(0, os.path.abspath(ESTRUTURA_DIR))

from AbstractGraph import AbstractGraph  # type: ignore[reportMissingImports]


class MetricasDeComunidade:
	"""Calcula métricas de comunidade para um grafo direcionado simples."""

	def __init__(self, grafo: AbstractGraph) -> None:
		self.grafo = grafo
		self._vertices = list(range(self.grafo.getVertexCount()))
		self._arestas_nao_direcionadas = self._construir_arestas_nao_direcionadas()
		self._adjacencia_nao_direcionada = self._construir_adjacencia_nao_direcionada()

	def detectar_comunidades(self, max_iteracoes: int = 50) -> Dict[int, List[int]]:
		"""Detecta comunidades usando label propagation sem bibliotecas externas.

		O algoritmo parte de um rótulo por vértice e, a cada iteração, cada
		vértice adota o rótulo mais frequente entre seus vizinhos. Em empates,
		o menor rótulo é escolhido para manter determinismo.
		"""
		labels = {vertice: vertice for vertice in self._vertices}

		for _ in range(max_iteracoes):
			alterou = False

			for vertice in self._vertices:
				vizinhos = self._adjacencia_nao_direcionada.get(vertice, set())
				if not vizinhos:
					continue

				frequencias = Counter(labels[vizinho] for vizinho in vizinhos)
				maior_freq = max(frequencias.values())
				candidatos = [rotulo for rotulo, freq in frequencias.items() if freq == maior_freq]
				novo_rotulo = min(candidatos)

				if labels[vertice] != novo_rotulo:
					labels[vertice] = novo_rotulo
					alterou = True

			if not alterou:
				break

		comunidades: Dict[int, List[int]] = defaultdict(list)
		for vertice, rotulo in labels.items():
			comunidades[rotulo].append(vertice)

		return {rotulo: sorted(membros) for rotulo, membros in sorted(comunidades.items(), key=lambda item: item[0])}

	def calcular_modularidade(self, comunidades: Mapping[int, Sequence[int]] | None = None) -> float:
		"""Calcula a modularidade da partição de comunidades encontrada.

		A modularidade mede o quanto as arestas internas de cada comunidade são
		mais frequentes do que seria esperado ao acaso.
		"""
		if comunidades is None:
			comunidades = self.detectar_comunidades()

		total_arestas = len(self._arestas_nao_direcionadas)
		if total_arestas == 0:
			return 0.0

		graus = {vertice: len(self._adjacencia_nao_direcionada.get(vertice, set())) for vertice in self._vertices}
		duas_m = 2 * total_arestas
		modularidade = 0.0

		for membros in comunidades.values():
			membros_set = set(membros)
			if not membros_set:
				continue

			for u in membros_set:
				for v in membros_set:
					a_ij = 1.0 if self._existe_aresta_nao_direcionada(u, v) else 0.0
					modularidade += a_ij - (graus[u] * graus[v]) / duas_m

		return modularidade / duas_m

	def detectar_bridging_ties(self, comunidades: Mapping[int, Sequence[int]] | None = None) -> List[Dict[str, object]]:
		"""Identifica vértices que ligam comunidades diferentes.

		Um bridging tie aqui é um vértice que possui vizinhos em mais de uma
		comunidade e cuja distribuição de conexões atravessa grupos diferentes.
		O resultado é ordenado pelo maior índice de intermediação entre
		comunidades.
		"""
		if comunidades is None:
			comunidades = self.detectar_comunidades()

		comunidade_por_vertice = self._mapear_vertice_para_comunidade(comunidades)
		resultados: List[Dict[str, object]] = []

		for vertice in self._vertices:
			vizinhos = self._adjacencia_nao_direcionada.get(vertice, set())
			if len(vizinhos) < 2:
				continue

			comunidades_vizinhanca = Counter()
			for vizinho in vizinhos:
				comunidade_vizinhanca = comunidade_por_vertice.get(vizinho)
				if comunidade_vizinhanca is not None:
					comunidades_vizinhanca[comunidade_vizinhanca] += 1

			comunidades_distintas = len(comunidades_vizinhanca)
			if comunidades_distintas < 2:
				continue

			total = sum(comunidades_vizinhanca.values())
			maior = max(comunidades_vizinhanca.values())
			indice_intermediacao = 1.0 - (maior / total)

			resultados.append(
				{
					"vertice": vertice,
					"label": self.grafo.getVertexLabel(vertice) or str(vertice),
					"comunidades_vizinhas": comunidades_distintas,
					"indice_intermediacao": round(indice_intermediacao, 6),
					"comunidade_atual": comunidade_por_vertice.get(vertice),
					"grau": len(vizinhos),
				}
			)

		resultados.sort(key=lambda item: (-item["indice_intermediacao"], -item["grau"], item["vertice"]))
		return resultados

	def resumo(self) -> Dict[str, object]:
		"""Retorna um resumo consolidado das métricas de comunidade."""
		comunidades = self.detectar_comunidades()
		bridging_ties = self.detectar_bridging_ties(comunidades)

		return {
			"num_vertices": self.grafo.getVertexCount(),
			"num_arestas_nao_direcionadas": len(self._arestas_nao_direcionadas),
			"num_comunidades": len(comunidades),
			"comunidades": [
				{
					"id": comunidade_id,
					"tamanho": len(membros),
					"membros": [self.grafo.getVertexLabel(v) or str(v) for v in membros],
				}
				for comunidade_id, membros in comunidades.items()
			],
			"modularidade": round(self.calcular_modularidade(comunidades), 6),
			"bridging_ties": bridging_ties,
		}

	def salvar(self, diretorio_saida: Path) -> Dict[str, object]:
		"""Salva o resumo em JSON e retorna os dados gerados."""
		diretorio_saida = Path(diretorio_saida)
		diretorio_saida.mkdir(parents=True, exist_ok=True)

		resultado = self.resumo()
		arquivo_saida = diretorio_saida / "metricas_comunidade.json"

		with arquivo_saida.open("w", encoding="utf-8") as arquivo:
			json.dump(resultado, arquivo, ensure_ascii=False, indent=2)

		return resultado

	def _construir_arestas_nao_direcionadas(self) -> Dict[Tuple[int, int], float]:
		arestas: Dict[Tuple[int, int], float] = {}

		for i, u in enumerate(self._vertices):
			for v in self._vertices[i + 1 :]:
				peso = 0.0

				if self.grafo.hasEdge(u, v):
					peso += float(self.grafo.getEdgeWeight(u, v))

				if self.grafo.hasEdge(v, u):
					peso += float(self.grafo.getEdgeWeight(v, u))

				if peso > 0.0:
					arestas[(u, v)] = peso

		return arestas

	def _construir_adjacencia_nao_direcionada(self) -> Dict[int, Set[int]]:
		adjacencia: Dict[int, Set[int]] = {vertice: set() for vertice in self._vertices}

		for (u, v), _peso in self._arestas_nao_direcionadas.items():
			adjacencia[u].add(v)
			adjacencia[v].add(u)

		return adjacencia

	def _mapear_vertice_para_comunidade(self, comunidades: Mapping[int, Sequence[int]]) -> Dict[int, int]:
		mapa: Dict[int, int] = {}
		for comunidade_id, membros in comunidades.items():
			for vertice in membros:
				mapa[vertice] = comunidade_id
		return mapa

	def _existe_aresta_nao_direcionada(self, u: int, v: int) -> bool:
		if u == v:
			return False

		return self.grafo.hasEdge(u, v) or self.grafo.hasEdge(v, u)


def analisar_comunidades(grafo: AbstractGraph, arquivo_saida: Path | None = None) -> Dict[str, object]:
	"""Atalho funcional para analisar comunidades de um grafo já construído."""
	analisador = MetricasDeComunidade(grafo)

	if arquivo_saida is not None:
		return analisador.salvar(arquivo_saida)

	return analisador.resumo()


if __name__ == "__main__":
	print("Este módulo espera um grafo já construído para gerar as métricas de comunidade.")
