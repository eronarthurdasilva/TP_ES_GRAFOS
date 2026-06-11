"""
Métricas de centralidade para grafos direcionados do projeto.

Este módulo foi criado para o trabalho de estrutura de dados e grafos,
oferecendo cálculos que podem ser aplicados a qualquer grafo que implemente
as operações básicas definidas em AbstractGraph.

Neste projeto, a centralidade é usada para medir a importância dos vértices
na rede de colaboração do GitHub.
"""

from __future__ import annotations

from typing import Dict, List


def _vertex_range(graph) -> range:
    return range(graph.getVertexCount())


def _successors(graph, u: int) -> List[int]:
    return [v for v in _vertex_range(graph) if u != v and graph.hasEdge(u, v)]


def _predecessors(graph, u: int) -> List[int]:
    return [v for v in _vertex_range(graph) if u != v and graph.hasEdge(v, u)]


def _out_weight_sum(graph, u: int) -> float:
    total = 0.0
    for v in _successors(graph, u):
        total += graph.getEdgeWeight(u, v)
    return total


def calculate_in_degree_centrality(graph, normalized: bool = True) -> Dict[int, float]:
    n = graph.getVertexCount()
    if n == 0:
        return {}

    factor = 1.0 / (n - 1) if normalized and n > 1 else 1.0
    return {u: graph.getVertexInDegree(u) * factor for u in _vertex_range(graph)}


def calculate_out_degree_centrality(graph, normalized: bool = True) -> Dict[int, float]:
    n = graph.getVertexCount()
    if n == 0:
        return {}

    factor = 1.0 / (n - 1) if normalized and n > 1 else 1.0
    return {u: graph.getVertexOutDegree(u) * factor for u in _vertex_range(graph)}


def calculate_degree_centrality(graph, normalized: bool = True) -> Dict[int, float]:
    n = graph.getVertexCount()
    if n == 0:
        return {}

    factor = 1.0 / (2 * (n - 1)) if normalized and n > 1 else 1.0
    return {
        u: (graph.getVertexInDegree(u) + graph.getVertexOutDegree(u)) * factor
        for u in _vertex_range(graph)
    }


def calculate_pagerank(
    graph,
    damping: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-6,
) -> Dict[int, float]:
    n = graph.getVertexCount()
    if n == 0:
        return {}

    ranks = {u: 1.0 / n for u in _vertex_range(graph)}

    for _ in range(max_iter):
        next_ranks: Dict[int, float] = {}
        sink_rank = 0.0

        for u in _vertex_range(graph):
            if _out_weight_sum(graph, u) == 0.0:
                sink_rank += ranks[u]

        diff = 0.0
        for u in _vertex_range(graph):
            rank = (1.0 - damping) / n
            rank += damping * sink_rank / n

            for v in _predecessors(graph, u):
                out_sum = _out_weight_sum(graph, v)
                if out_sum > 0.0:
                    rank += damping * ranks[v] * (graph.getEdgeWeight(v, u) / out_sum)

            next_ranks[u] = rank
            diff += abs(rank - ranks[u])

        ranks = next_ranks
        if diff < tol:
            break

    return ranks


def apply_vertex_weights(graph, centrality: Dict[int, float]) -> None:
    for u, weight in centrality.items():
        graph.setVertexWeight(u, weight)
