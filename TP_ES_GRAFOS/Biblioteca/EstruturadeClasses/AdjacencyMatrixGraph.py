"""
AdjacencyMatrixGraph.py
=======================
Implementação concreta de grafo direcionado simples usando MATRIZ DE ADJACÊNCIA.

O que é matriz de adjacência?
    Uma matriz quadrática n×n onde:
        matrix[u][v] != 0  →  existe aresta u → v (valor = peso da aresta)
        matrix[u][v] == 0  →  não existe aresta u → v

    Exemplo com 4 vértices:
              destino
              0     1     2     3
    origem 0 [0.0] [2.0] [0.0] [0.0]   → vértice 0 tem aresta para 1 (peso 2)
           1 [0.0] [0.0] [5.0] [0.0]   → vértice 1 tem aresta para 2 (peso 5)
           2 [0.0] [0.0] [0.0] [3.0]   → vértice 2 tem aresta para 3 (peso 3)
           3 [4.0] [0.0] [0.0] [0.0]   → vértice 3 tem aresta para 0 (peso 4)

Vantagens da matriz:
    - hasEdge(u, v) em O(1) — acesso direto por índice
    - addEdge e removeEdge em O(1)

Desvantagens:
    - Memória O(n²) — mesmo que o grafo tenha poucas arestas
    - Para grafos esparsos (poucas arestas), lista é mais eficiente
"""

import xml.etree.ElementTree as ET
from typing import List

from AbstractGraph import AbstractGraph


class AdjacencyMatrixGraph(AbstractGraph):
    """
    Grafo direcionado simples com pesos, armazenado em matriz de adjacência.

    Herda de AbstractGraph:
        - _num_vertices, _vertex_weights, _vertex_labels
        - _validar_vertice, _validar_aresta
        - setVertexWeight, getVertexWeight, setVertexLabel, getVertexLabel
        - isSucessor, isPredecessor, isDivergent, isConvergent, isIncident
    """

    def __init__(self, num_vertices: int) -> None:
        """
        Cria um grafo com num_vertices vértices e nenhuma aresta.

        Chama super().__init__() para inicializar os atributos herdados,
        depois cria a matriz n×n preenchida com 0.0 (sem arestas).

        Args:
            num_vertices: Número de vértices. Deve ser > 0.

        Exemplo:
            g = AdjacencyMatrixGraph(4)
            # cria matriz 4×4 toda zerada
        """
        # Inicializa atributos da classe pai (num_vertices, vertex_weights, labels)
        super().__init__(num_vertices)

        # Matriz n×n de floats — cada célula representa o peso de uma aresta
        # 0.0 significa "aresta não existe"
        # Usamos lista de listas: matrix[linha][coluna] = matrix[origem][destino]
        self._matrix: List[List[float]] = [
            [0.0] * num_vertices
            for _ in range(num_vertices)
        ]

    # ─────────────────────────────────────────────────────────────────────────
    # CONTAGEM
    # ─────────────────────────────────────────────────────────────────────────

    def getVertexCount(self) -> int:
        """
        Retorna o número de vértices do grafo.

        Simplesmente retorna o atributo herdado de AbstractGraph.

        Returns:
            Número de vértices definido no construtor.
        """
        return self._num_vertices

    def getEdgeCount(self) -> int:
        """
        Conta quantas arestas existem percorrendo a matriz inteira.

        Como funciona:
            Percorre todas as células matrix[u][v].
            Se matrix[u][v] != 0.0, existe uma aresta u → v.
            Soma 1 para cada aresta encontrada.

        Complexidade: O(n²) — percorre toda a matriz.

        Returns:
            Número total de arestas.
        """
        count = 0
        for u in range(self._num_vertices):
            for v in range(self._num_vertices):
                if self._matrix[u][v] != 0.0:
                    count += 1
        return count

    # ─────────────────────────────────────────────────────────────────────────
    # OPERAÇÕES DE ARESTA
    # ─────────────────────────────────────────────────────────────────────────

    def hasEdge(self, u: int, v: int) -> bool:
        """
        Verifica se existe aresta de u para v.

        Como funciona:
            Acessa diretamente matrix[u][v].
            Se != 0.0, a aresta existe.

        Complexidade: O(1) — acesso direto por índice.

        Args:
            u: Vértice de origem.
            v: Vértice de destino.

        Returns:
            True se matrix[u][v] != 0.0.
        """
        self._validar_aresta(u, v)
        return self._matrix[u][v] != 0.0

    def addEdge(self, u: int, v: int) -> None:
        """
        Adiciona aresta direcionada u → v com peso padrão 1.0.

        Idempotente: se a aresta já existe, não faz nada (não duplica).
        Isso atende ao requisito do enunciado.

        Como funciona:
            Se matrix[u][v] == 0.0 → aresta não existe → define como 1.0
            Se matrix[u][v] != 0.0 → aresta já existe → ignora

        Complexidade: O(1).

        Args:
            u: Vértice de origem.
            v: Vértice de destino.
        """
        self._validar_aresta(u, v)

        # Idempotência: só adiciona se ainda não existe
        if self._matrix[u][v] == 0.0:
            self._matrix[u][v] = 1.0   # peso padrão = 1.0

    def removeEdge(self, u: int, v: int) -> None:
        """
        Remove a aresta direcionada u → v.

        Como funciona:
            Define matrix[u][v] = 0.0 (volta ao estado "sem aresta").
            Se a aresta não existe, lança ValueError.

        Complexidade: O(1).

        Args:
            u: Vértice de origem.
            v: Vértice de destino.

        Raises:
            ValueError: Se a aresta u → v não existir.
        """
        self._validar_aresta(u, v)

        if self._matrix[u][v] == 0.0:
            raise ValueError(f"Aresta {u} → {v} não existe e não pode ser removida.")

        self._matrix[u][v] = 0.0

    def setEdgeWeight(self, u: int, v: int, w: float) -> None:
        """
        Define o peso da aresta u → v.

        No projeto de colaboração:
            peso 2 = comentário
            peso 3 = fechamento
            peso 4 = aprovação/revisão
            peso 5 = merge

        Se a aresta não existir, ela é criada com o peso fornecido.

        Como funciona:
            Simplesmente define matrix[u][v] = w.
            Como 0.0 significa "sem aresta", w deve ser != 0.

        Args:
            u: Vértice de origem.
            v: Vértice de destino.
            w: Peso da aresta (deve ser != 0.0).

        Raises:
            ValueError: Se w == 0.0 (confundiria com "sem aresta").
        """
        self._validar_aresta(u, v)

        if w == 0.0:
            raise ValueError(
                "Peso 0.0 não é permitido — use removeEdge para remover a aresta."
            )

        self._matrix[u][v] = w

    def getEdgeWeight(self, u: int, v: int) -> float:
        """
        Retorna o peso da aresta u → v.

        Como funciona:
            Acessa matrix[u][v].
            Se for 0.0, a aresta não existe → lança ValueError.

        Complexidade: O(1).

        Args:
            u: Vértice de origem.
            v: Vértice de destino.

        Returns:
            Peso da aresta (float).

        Raises:
            ValueError: Se a aresta u → v não existir.
        """
        self._validar_aresta(u, v)

        if self._matrix[u][v] == 0.0:
            raise ValueError(f"Aresta {u} → {v} não existe.")

        return self._matrix[u][v]

    # ─────────────────────────────────────────────────────────────────────────
    # GRAUS
    # ─────────────────────────────────────────────────────────────────────────

    def getVertexInDegree(self, u: int) -> int:
        """
        Retorna o grau de entrada de u — quantas arestas CHEGAM em u.

        Como funciona na matriz:
            Percorre a COLUNA u (todos os vértices que apontam para u).
            Conta quantas células != 0.0 nessa coluna.

        Visualização (coluna 1 = grau de entrada do vértice 1):
                  col 1
            [0.0] [2.0]   ← linha 0: existe aresta 0→1
            [0.0] [0.0]   ← linha 1: sem aresta 1→1
            [0.0] [3.0]   ← linha 2: existe aresta 2→1
            InDegree(1) = 2

        Complexidade: O(n) — percorre uma coluna inteira.

        Args:
            u: Índice do vértice.

        Returns:
            Número de arestas que chegam em u.
        """
        self._validar_vertice(u)

        # Percorre todos os vértices v e verifica se existe aresta v → u
        return sum(
            1 for v in range(self._num_vertices)
            if self._matrix[v][u] != 0.0
        )

    def getVertexOutDegree(self, u: int) -> int:
        """
        Retorna o grau de saída de u — quantas arestas PARTEM de u.

        Como funciona na matriz:
            Percorre a LINHA u (todos os vértices para onde u aponta).
            Conta quantas células != 0.0 nessa linha.

        Visualização (linha 0 = grau de saída do vértice 0):
            linha 0: [0.0, 2.0, 0.0, 5.0]
            OutDegree(0) = 2  (arestas 0→1 e 0→3)

        Complexidade: O(n) — percorre uma linha inteira.

        Args:
            u: Índice do vértice.

        Returns:
            Número de arestas que partem de u.
        """
        self._validar_vertice(u)

        # Percorre todos os vértices v e verifica se existe aresta u → v
        return sum(
            1 for v in range(self._num_vertices)
            if self._matrix[u][v] != 0.0
        )

    # ─────────────────────────────────────────────────────────────────────────
    # PROPRIEDADES DO GRAFO
    # ─────────────────────────────────────────────────────────────────────────

    def isEmptyGraph(self) -> bool:
        """
        Verifica se o grafo é vazio (sem nenhuma aresta).

        Como funciona:
            Verifica se getEdgeCount() == 0.
            Grafo vazio tem vértices mas nenhuma aresta.

        Returns:
            True se não existir nenhuma aresta.
        """
        return super().isEmptyGraph()

    def isCompleteGraph(self) -> bool:
        """
        Verifica se o grafo é completo.

        Grafo direcionado completo:
            Existe aresta entre TODO par ordenado (u, v) onde u != v.
            Para n vértices: n * (n-1) arestas no total.

            Exemplo com n=3:
                0→1, 0→2  (2 saindo de 0)
                1→0, 1→2  (2 saindo de 1)
                2→0, 2→1  (2 saindo de 2)
                Total: 6 = 3 * (3-1)

        Returns:
            True se o número de arestas == n * (n - 1).
        """
        return super().isCompleteGraph()

    def isConnected(self) -> bool:
        """
        Verifica se o grafo é fortemente conexo.

        Fortemente conexo: existe caminho de QUALQUER vértice para QUALQUER outro.

        Algoritmo — dois BFS:
            1. BFS normal a partir do vértice 0 no grafo original
               → verifica se todos os vértices são alcançáveis saindo de 0

            2. BFS no grafo TRANSPOSTO (todas as arestas invertidas) a partir de 0
               → verifica se todos os vértices conseguem CHEGAR em 0

            Se ambos visitarem todos os n vértices → grafo é fortemente conexo.

        Por que transposto?
            No grafo original, BFS de 0 mostra quem 0 alcança.
            No transposto, BFS de 0 mostra quem consegue alcançar 0 no original.
            Se ambos cobrem todos → qualquer par (u, v) tem caminho.

        Complexidade: O(n²) — BFS em matriz percorre linhas inteiras.

        Returns:
            True se o grafo for fortemente conexo.
        """
        return super().isConnected()

    # ─────────────────────────────────────────────────────────────────────────
    # EXPORTAÇÃO GEPHI
    # ─────────────────────────────────────────────────────────────────────────

    def exportToGEPHI(self, path: str) -> None:
        """
        Exporta o grafo no formato GEXF para visualização no GEPHI.

        GEXF = Graph Exchange XML Format.
        É um dos formatos nativamente suportados pelo GEPHI.

        Estrutura do arquivo gerado:
            <gexf>
              <graph defaultedgetype="directed">
                <nodes>
                  <node id="0" label="vaxry" />
                  ...
                </nodes>
                <edges>
                  <edge id="0" source="0" target="1" weight="2.0" />
                  ...
                </edges>
              </graph>
            </gexf>

        Args:
            path: Caminho do arquivo de saída (ex: "grafo_comentarios.gexf").
        """
        # Elemento raiz do XML
        gexf = ET.Element("gexf", {
            "xmlns":   "http://gexf.net/1.3",
            "version": "1.3"
        })

        # Elemento <graph> — directed = grafo direcionado
        graph = ET.SubElement(gexf, "graph", {
            "defaultedgetype": "directed"
        })

        # ── Nós ───────────────────────────────────────────────────────────
        nodes_el = ET.SubElement(graph, "nodes")

        for v in range(self._num_vertices):
            label = self._vertex_labels[v] or str(v)  # usa índice se sem label
            ET.SubElement(nodes_el, "node", {
                "id":    str(v),
                "label": label,
            })

        # ── Arestas ────────────────────────────────────────────────────────
        edges_el = ET.SubElement(graph, "edges")
        edge_id  = 0

        for u in range(self._num_vertices):
            for v in range(self._num_vertices):
                if self._matrix[u][v] != 0.0:
                    ET.SubElement(edges_el, "edge", {
                        "id":     str(edge_id),
                        "source": str(u),
                        "target": str(v),
                        "weight": str(self._matrix[u][v]),
                    })
                    edge_id += 1

        # Serializa e salva o XML
        tree = ET.ElementTree(gexf)
        ET.indent(tree, space="  ")   # indentação para legibilidade

        with open(path, "wb") as f:
            tree.write(f, encoding="utf-8", xml_declaration=True)

        print(f"Grafo exportado para GEPHI: {path}")