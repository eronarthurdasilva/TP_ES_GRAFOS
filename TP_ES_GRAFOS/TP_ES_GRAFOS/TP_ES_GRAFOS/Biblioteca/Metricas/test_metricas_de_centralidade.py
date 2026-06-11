from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from EstruturadeClasses.AdjacencyListGraph import AdjacencyListGraph
from Metricas.MetricasDeCentralidade import (
    apply_vertex_weights,
    calculate_degree_centrality,
    calculate_in_degree_centrality,
    calculate_out_degree_centrality,
    calculate_pagerank,
)


def run_tests() -> None:
    graph = AdjacencyListGraph(4)
    graph.addEdge(0, 1)
    graph.addEdge(0, 2)
    graph.addEdge(1, 2)
    graph.addEdge(2, 3)

    indegree = calculate_in_degree_centrality(graph, normalized=False)
    assert indegree == {0: 0, 1: 1, 2: 2, 3: 1}

    outdegree = calculate_out_degree_centrality(graph, normalized=False)
    assert outdegree == {0: 2, 1: 1, 2: 1, 3: 0}

    degree = calculate_degree_centrality(graph, normalized=False)
    assert degree == {0: 2, 1: 2, 2: 3, 3: 1}

    pagerank = calculate_pagerank(graph, damping=0.85, max_iter=200, tol=1e-9)
    assert abs(sum(pagerank.values()) - 1.0) < 1e-9

    apply_vertex_weights(graph, pagerank)
    assert abs(graph.getVertexWeight(0) - pagerank[0]) < 1e-12

    print("MetricasDeCentralidade: todos os testes passaram.")


if __name__ == "__main__":
    run_tests()
