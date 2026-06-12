"""
AdjacencyListGraph.py
=====================
Implementação concreta de grafo direcionado simples usando LISTA DE ADJACÊNCIA.

O que é lista de adjacência?
    Para cada vértice u, mantemos uma estrutura com os vértices que u aponta para.
    Usamos um dicionário: adjacencyList[u] = {v: peso, ...}
    
    Exemplo com 4 vértices:
        adjacencyList[0] = {1: 2.0}              → vértice 0 aponta para 1 (peso 2)
        adjacencyList[1] = {2: 5.0}              → vértice 1 aponta para 2 (peso 5)
        adjacencyList[2] = {3: 3.0}              → vértice 2 aponta para 3 (peso 3)
        adjacencyList[3] = {0: 4.0}              → vértice 3 aponta para 0 (peso 4)

Vantagens da lista:
    - Memória O(n + m) — só armazena arestas que existem
    - Melhor para grafos esparsos (poucas arestas)

Desvantagens:
    - hasEdge(u, v) em O(grau(u)) — precisa procurar na lista
    - Menos cache-friendly que matriz
"""

import xml.etree.ElementTree as ET
from typing import Dict

from AbstractGraph import AbstractGraph


class AdjacencyListGraph(AbstractGraph):
    """
    Grafo direcionado simples com pesos, armazenado em lista de adjacência.
    
    Estrutura interna:
        _adjacency_list: Dict[int, Dict[int, float]]
        - Para cada vértice u (chave), temos um dicionário {v: peso}
        - adjacency_list[u][v] = peso da aresta u → v
    
    Herda de AbstractGraph:
        - _num_vertices, _vertex_weights, _vertex_labels
        - _validar_vertice, _validar_aresta
        - setVertexWeight, getVertexWeight, setVertexLabel, getVertexLabel
        - isSucessor, isPredecessor, isDivergent, isConvergent, isIncident
    """

    def __init__(self, num_vertices: int) -> None:
        """
        Cria um grafo com num_vertices vértices e nenhuma aresta.
        
        Inicializa a lista de adjacência com um dicionário vazio para cada vértice.
        
        Args:
            num_vertices: Número de vértices. Deve ser > 0.
            
        Exemplo:
            g = AdjacencyListGraph(4)
            # cria lista de adjacência com 4 vértices vazios
        """
        super().__init__(num_vertices)
        
        # adjacency_list[u] = {v: peso} para cada aresta u → v
        # Inicializado vazio — sem arestas
        self._adjacency_list: Dict[int, Dict[int, float]] = {
            u: {} for u in range(num_vertices)
        }

    # ─────────────────────────────────────────────────────────────────────────
    # CONTAGEM
    # ─────────────────────────────────────────────────────────────────────────

    def getVertexCount(self) -> int:
        """
        Retorna o número de vértices do grafo.
        
        Returns:
            Número de vértices definido no construtor.
        """
        return self._num_vertices

    def getEdgeCount(self) -> int:
        """
        Conta quantas arestas existem somando os tamanhos das listas.
        
        Como funciona:
            Para cada vértice u, conta quantos vértices existem em adjacency_list[u].
            Soma o total de arestas.
        
        Complexidade: O(n) — itera sobre cada vértice uma vez.
        
        Returns:
            Número total de arestas.
        """
        return sum(len(neighbors) for neighbors in self._adjacency_list.values())

    # ─────────────────────────────────────────────────────────────────────────
    # OPERAÇÕES DE ARESTA
    # ─────────────────────────────────────────────────────────────────────────

    def hasEdge(self, u: int, v: int) -> bool:
        """
        Verifica se existe aresta de u para v.
        
        Como funciona:
            Verifica se v está nas chaves de adjacency_list[u].
        
        Complexidade: O(1) em média (lookup de dicionário).
        
        Args:
            u: Vértice de origem.
            v: Vértice de destino.
        
        Returns:
            True se v está em adjacency_list[u].
        """
        self._validar_aresta(u, v)
        return v in self._adjacency_list[u]

    def addEdge(self, u: int, v: int) -> None:
        """
        Adiciona aresta direcionada u → v com peso padrão 1.0.
        
        Idempotente: se a aresta já existe, não faz nada (não duplica).
        
        Como funciona:
            Se v não está em adjacency_list[u], adiciona com peso 1.0.
            Se v já existe, ignora (idempotência).
        
        Complexidade: O(1) em média.
        
        Args:
            u: Vértice de origem.
            v: Vértice de destino.
        """
        self._validar_aresta(u, v)
        
        # Idempotência: só adiciona se ainda não existe
        if v not in self._adjacency_list[u]:
            self._adjacency_list[u][v] = 1.0  # peso padrão

    def removeEdge(self, u: int, v: int) -> None:
        """
        Remove a aresta direcionada u → v.
        
        Como funciona:
            Remove v de adjacency_list[u].
            Se a aresta não existe, lança ValueError.
        
        Complexidade: O(1) em média (dicionário).
        
        Args:
            u: Vértice de origem.
            v: Vértice de destino.
        
        Raises:
            ValueError: Se a aresta u → v não existir.
        """
        self._validar_aresta(u, v)
        
        if v not in self._adjacency_list[u]:
            raise ValueError(f"Aresta {u} → {v} não existe e não pode ser removida.")
        
        del self._adjacency_list[u][v]

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
            Define adjacency_list[u][v] = w.
            w não deve ser 0.0 (para evitar confusão com "aresta não existe").
        
        Args:
            u: Vértice de origem.
            v: Vértice de destino.
            w: Peso da aresta (deve ser != 0.0).
        
        Raises:
            ValueError: Se w == 0.0.
        """
        self._validar_aresta(u, v)
        
        if w == 0.0:
            raise ValueError(
                "Peso 0.0 não é permitido — use removeEdge para remover a aresta."
            )
        
        self._adjacency_list[u][v] = w

    def getEdgeWeight(self, u: int, v: int) -> float:
        """
        Retorna o peso da aresta u → v.
        
        Como funciona:
            Acessa adjacency_list[u][v].
            Se não existir, lança ValueError.
        
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
        
        if v not in self._adjacency_list[u]:
            raise ValueError(f"Aresta {u} → {v} não existe.")
        
        return self._adjacency_list[u][v]

    # ─────────────────────────────────────────────────────────────────────────
    # GRAUS
    # ─────────────────────────────────────────────────────────────────────────

    def getVertexInDegree(self, u: int) -> int:
        """
        Retorna o grau de entrada de u — quantas arestas CHEGAM em u.
        
        Como funciona na lista:
            Percorre TODOS os vértices v e conta quantos têm u em sua lista.
            count += 1 se v → u existe
        
        Complexidade: O(n + m) — pior caso percorre lista inteira.
        
        Args:
            u: Índice do vértice.
        
        Returns:
            Número de arestas que chegam em u.
        """
        self._validar_vertice(u)
        
        count = 0
        for v in range(self._num_vertices):
            if u in self._adjacency_list[v]:
                count += 1
        
        return count

    def getVertexOutDegree(self, u: int) -> int:
        """
        Retorna o grau de saída de u — quantas arestas PARTEM de u.
        
        Como funciona na lista:
            Simplesmente conta quantos vértices estão em adjacency_list[u].
        
        Complexidade: O(1) — len() de dicionário é O(1).
        
        Args:
            u: Índice do vértice.
        
        Returns:
            Número de arestas que partem de u.
        """
        self._validar_vertice(u)
        return len(self._adjacency_list[u])

    # ─────────────────────────────────────────────────────────────────────────
    # PROPRIEDADES DO GRAFO
    # ─────────────────────────────────────────────────────────────────────────

    def isEmptyGraph(self) -> bool:
        """
        Verifica se o grafo é vazio (sem nenhuma aresta).
        
        Returns:
            True se getEdgeCount() == 0.
        """
        return super().isEmptyGraph()

    def isCompleteGraph(self) -> bool:
        """
        Verifica se o grafo é completo.
        
        Grafo direcionado completo:
            Existe aresta entre TODO par ordenado (u, v) onde u != v.
            Para n vértices: n * (n-1) arestas no total.
        
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
            
            2. BFS no grafo TRANSPOSTO a partir de 0
               → verifica se todos conseguem CHEGAR em 0
            
            Se ambos visitarem todos → grafo é fortemente conexo.
        
        Complexidade: O(n + m) — BFS em lista de adjacência.
        
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
        Formato nativo do GEPHI para visualização de grafos.
        
        Args:
            path: Caminho do arquivo de saída (ex: "grafo_comentarios.gexf").
        """
        # Elemento raiz do XML
        gexf = ET.Element("gexf", {
            "xmlns": "http://gexf.net/1.3",
            "version": "1.3"
        })

        # Elemento <graph> — directed = grafo direcionado
        graph = ET.SubElement(gexf, "graph", {
            "defaultedgetype": "directed"
        })

        # ── Nós ────────────────────────────────────────────────────────────
        nodes_el = ET.SubElement(graph, "nodes")

        for v in range(self._num_vertices):
            label = self._vertex_labels[v] or str(v)  # usa índice se sem label
            ET.SubElement(nodes_el, "node", {
                "id": str(v),
                "label": label,
            })

        # ── Arestas ─────────────────────────────────────────────────────────
        edges_el = ET.SubElement(graph, "edges")
        edge_id = 0

        for u in range(self._num_vertices):
            for v, weight in self._adjacency_list[u].items():
                ET.SubElement(edges_el, "edge", {
                    "id": str(edge_id),
                    "source": str(u),
                    "target": str(v),
                    "weight": str(weight),
                })
                edge_id += 1

        # Serializa e salva o XML
        tree = ET.ElementTree(gexf)
        ET.indent(tree, space="  ")  # indentação para legibilidade

        with open(path, "wb") as f:
            tree.write(f, encoding="utf-8", xml_declaration=True)

        print(f"Grafo exportado para GEPHI: {path}")