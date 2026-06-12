"""
AbstractGraph.py
================
Classe base abstrata para grafos direcionados simples.

O que é uma classe abstrata?
    É uma classe que define O CONTRATO — quais métodos toda implementação
    concreta deve ter — mas não implementa a lógica de armazenamento.
    É como uma "planta" que AdjacencyMatrixGraph e AdjacencyListGraph seguem.

Por que usar ABC?
    Se uma subclasse esquecer de implementar algum método @abstractmethod,
    Python lança TypeError na hora de instanciar — antes de qualquer bug em runtime.

Hierarquia:
    AbstractGraph (esta classe)
        ├── AdjacencyMatrixGraph  → armazena arestas em matriz n×n
        └── AdjacencyListGraph   → armazena arestas em dicionário de listas
"""

from abc import ABC, abstractmethod
from collections import deque
from typing import List


class AbstractGraph(ABC):
    """
    Define a API comum para grafos direcionados simples com pesos.

    Grafo SIMPLES significa:
        - Sem laços (self-loops): não existe aresta de u para u
        - Sem múltiplas arestas: no máximo uma aresta de u para v

    Grafo DIRECIONADO significa:
        - Aresta (u → v) não implica aresta (v → u)
        - Para relação bidirecional, usa-se arestas antiparalelas: (u→v) e (v→u)
    """

    # ─────────────────────────────────────────────────────────────────────────
    # CONSTRUTOR
    # ─────────────────────────────────────────────────────────────────────────

    def __init__(self, num_vertices: int) -> None:
        """
        Inicializa os atributos compartilhados por TODAS as implementações.

        Por que aqui e não nas subclasses?
            Pesos e rótulos de vértices são independentes de como as arestas
            são armazenadas (matriz ou lista). Centralizar evita duplicação.

        Args:
            num_vertices: Quantidade de vértices do grafo. Imutável após criação.

        Raises:
            ValueError: Se num_vertices for menor ou igual a zero.
        """
        if num_vertices <= 0:
            raise ValueError(
                f"Número de vértices deve ser positivo, recebeu: {num_vertices}"
            )

        # Quantidade de vértices — define o "tamanho" do grafo
        # Vértices são identificados por índices inteiros: 0, 1, 2, ..., n-1
        self._num_vertices: int = num_vertices

        # Peso de cada vértice — inicializado com 0.0
        # Exemplo: no grafo de colaboração, pode representar o PageRank do usuário
        # Índice: vertexWeights[v] = peso do vértice v
        self._vertex_weights: List[float] = [0.0] * num_vertices
        # Rótulo (label) de cada vértice — inicializado com string vazia
        # Índice: vertexLabels[v] = "vaxry" (login do vértice v)
        self._vertex_labels: List[str] = [""] * num_vertices

    # ─────────────────────────────────────────────────────────────────────────
    # VALIDADORES INTERNOS — usados por todos os métodos
    # ─────────────────────────────────────────────────────────────────────────

    def _validar_vertice(self, v: int) -> None:
        """
        Verifica se o índice v é um vértice válido do grafo.

            Sem validação, acessar self._vertex_weights[999] num grafo de 10
            vértices causaria IndexError genérico, sem indicar o problema real.
            Com validação, o erro é claro e acontece antes de qualquer operação.

        Args:
            v: Índice do vértice a validar.

        Raises:
            ValueError: Se v < 0 ou v >= num_vertices.
        """
        if not (0 <= v < self._num_vertices):
            raise ValueError(
                f"Vértice {v} inválido. O grafo tem vértices de 0 a {self._num_vertices - 1}."
            )

    def _validar_aresta(self, u: int, v: int) -> None:
        """
        Verifica se o par (u, v) é uma aresta válida para este grafo.

        Valida dois casos:
            1. Se u e v são vértices válidos (delega para _validar_vertice)
            2. Se u != v (grafo simples não permite laços)

        Args:
            u: Vértice de origem.
            v: Vértice de destino.

        Raises:
            ValueError: Se u ou v forem inválidos, ou se u == v (laço).
        """
        self._validar_vertice(u)
        self._validar_vertice(v)

        # Laço = aresta de um vértice para ele mesmo (u → u)
        # O enunciado proíbe explicitamente: "grafos devem ser simples"
        if u == v:
            raise ValueError(
                f"Laços não são permitidos neste grafo (tentativa: {u} → {v})."
            )

    # ─────────────────────────────────────────────────────────────────────────
    # PESOS E RÓTULOS DE VÉRTICES — implementados aqui (não abstratos)
    # ─────────────────────────────────────────────────────────────────────────
    # Por que não abstratos?
    #   A lógica é a mesma para matriz e lista — só acessa self._vertex_weights[v].
    #   Não faz sentido cada subclasse reimplementar a mesma coisa.

    def setVertexWeight(self, v: int, w: float) -> None:
        """
        Define o peso do vértice v.

        Exemplo de uso no projeto:
            Após calcular PageRank, armazenar a pontuação de cada colaborador.

        Args:
            v: Índice do vértice.
            w: Peso a atribuir (qualquer float).

        Raises:
            ValueError: Se v for um índice inválido.
        """
        self._validar_vertice(v)
        self._vertex_weights[v] = w

    def getVertexWeight(self, v: int) -> float:
        """
        Retorna o peso do vértice v.

        Args:
            v: Índice do vértice.

        Returns:
            Peso atual do vértice (padrão: 0.0).

        Raises:
            ValueError: Se v for um índice inválido.
        """
        self._validar_vertice(v)
        return self._vertex_weights[v]

    def setVertexLabel(self, v: int, label: str) -> None:
        """
        Define o rótulo (label) do vértice v.

        No projeto de colaboração: o rótulo é o login do GitHub.
        Exemplo: grafo.setVertexLabel(0, "vaxry")

        Args:
            v: Índice do vértice.
            label: String com o rótulo.

        Raises:
            ValueError: Se v for um índice inválido.
        """
        self._validar_vertice(v)
        self._vertex_labels[v] = label

    def getVertexLabel(self, v: int) -> str:
        """
        Retorna o rótulo do vértice v.

        Args:
            v: Índice do vértice.

        Returns:
            Rótulo atual do vértice (padrão: "").

        Raises:
            ValueError: Se v for um índice inválido.
        """
        self._validar_vertice(v)
        return self._vertex_labels[v]

    # ─────────────────────────────────────────────────────────────────────────
    # MÉTODOS CONCRETOS — lógica baseada em hasEdge(), igual pra toda subclasse
    # ─────────────────────────────────────────────────────────────────────────

    def isSucessor(self, u: int, v: int) -> bool:
        """
        Verifica se v é sucessor de u, ou seja, se existe aresta u → v.

        Conceito:
            No grafo direcionado, se existe (u → v), então:
            - v é sucessor de u
            - u é predecessor de v

        Args:
            u: Vértice de origem.
            v: Vértice de destino.

        Returns:
            True se existe aresta u → v.
        """
        self._validar_aresta(u, v)
        return self.hasEdge(u, v)

    def isPredecessor(self, u: int, v: int) -> bool:
        """
        Verifica se u é predecessor de v, ou seja, se existe aresta u → v.

        Nota: isPredecessor(u, v) == isSucessor(u, v)
              A diferença é semântica — quem pergunta muda o ponto de vista.
              isPredecessor(u, v): "u vem antes de v?"
              isSucessor(u, v):    "v vem depois de u?"

        Args:
            u: Possível predecessor.
            v: Possível sucessor.

        Returns:
            True se existe aresta u → v.
        """
        self._validar_aresta(u, v)
        return self.hasEdge(u, v)

    def isDivergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        """
        Verifica se as arestas (u1→v1) e (u2→v2) são divergentes.

        Arestas divergentes: partem do MESMO vértice de origem.
            u1 → v1
            u2 → v2
            onde u1 == u2

        Visualização:
                u ──→ v1
                └──→ v2
            (u "diverge" para dois destinos)

        Args:
            u1, v1: Primeira aresta.
            u2, v2: Segunda aresta.

        Returns:
            True se u1 == u2 e ambas as arestas existem.
        """
        self._validar_aresta(u1, v1)
        self._validar_aresta(u2, v2)
        return u1 == u2 and self.hasEdge(u1, v1) and self.hasEdge(u2, v2)

    def isConvergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        """
        Verifica se as arestas (u1→v1) e (u2→v2) são convergentes.

        Arestas convergentes: chegam no MESMO vértice de destino.
            u1 → v
            u2 → v
            onde v1 == v2

        Visualização:
            u1 ──→ v
            u2 ──→ /
            (dois vértices "convergem" para v)

        Args:
            u1, v1: Primeira aresta.
            u2, v2: Segunda aresta.

        Returns:
            True se v1 == v2 e ambas as arestas existem.
        """
        self._validar_aresta(u1, v1)
        self._validar_aresta(u2, v2)
        return v1 == v2 and self.hasEdge(u1, v1) and self.hasEdge(u2, v2)

    def isIncident(self, u: int, v: int, x: int) -> bool:
        """
        Verifica se o vértice x é incidente à aresta (u→v).

        Um vértice x é incidente a uma aresta se ele é a ORIGEM ou o DESTINO dela.
            isIncident(u, v, u) → True  (x é a origem)
            isIncident(u, v, v) → True  (x é o destino)
            isIncident(u, v, w) → False (w não tem relação com a aresta)

        Args:
            u: Origem da aresta.
            v: Destino da aresta.
            x: Vértice a verificar.

        Returns:
            True se x == u ou x == v e a aresta (u→v) existe.
        """
        self._validar_vertice(x)
        self._validar_aresta(u, v)

        # x precisa ser origem OU destino da aresta, E a aresta precisa existir
        return (x == u or x == v) and self.hasEdge(u, v)

    # ─────────────────────────────────────────────────────────────────────────
    # MÉTODOS ABSTRATOS — cada subclasse implementa do seu jeito
    # ─────────────────────────────────────────────────────────────────────────
    # @abstractmethod força a implementação nas subclasses.
    # Se AdjacencyMatrixGraph não implementar getEdgeCount(), Python lança:
    #     TypeError: Can't instantiate abstract class AdjacencyMatrixGraph
    #     with abstract method getEdgeCount

    @abstractmethod
    def getVertexCount(self) -> int:
        """
        Retorna o número de vértices do grafo.

        Returns:
            Número de vértices (definido no construtor).
        """

    @abstractmethod
    def getEdgeCount(self) -> int:
        """
        Retorna o número de arestas do grafo.

        Implementação varia:
            Matriz: conta células != 0 na matriz (dividido por 1, pois direcionado)
            Lista:  soma o tamanho de cada lista de adjacência

        Returns:
            Número de arestas existentes.
        """

    @abstractmethod
    def hasEdge(self, u: int, v: int) -> bool:
        """
        Verifica se existe aresta direcionada de u para v.

        Implementação varia:
            Matriz: verifica se matrix[u][v] != 0
            Lista:  verifica se v está na lista de adjacência de u

        Args:
            u: Vértice de origem.
            v: Vértice de destino.

        Returns:
            True se a aresta u → v existe.
        """

    @abstractmethod
    def addEdge(self, u: int, v: int) -> None:
        """
        Adiciona uma aresta direcionada de u para v.

        Restrições (enunciado):
            - Idempotente: adicionar aresta que já existe não faz nada (não duplica)
            - Não permite laços: u != v (validado em _validar_aresta)

        Args:
            u: Vértice de origem.
            v: Vértice de destino.
        """

    @abstractmethod
    def removeEdge(self, u: int, v: int) -> None:
        """
        Remove a aresta direcionada de u para v.

        Raises:
            ValueError: Se a aresta não existir.

        Args:
            u: Vértice de origem.
            v: Vértice de destino.
        """

    @abstractmethod
    def setEdgeWeight(self, u: int, v: int, w: float) -> None:
        """
        Define o peso da aresta u → v.

        No projeto de colaboração, o peso representa a intensidade da interação:
            Comentário = 2, Fechamento = 3, Aprovação = 4, Merge = 5

        Args:
            u: Vértice de origem.
            v: Vértice de destino.
            w: Peso da aresta.
        """

    @abstractmethod
    def getEdgeWeight(self, u: int, v: int) -> float:
        """
        Retorna o peso da aresta u → v.

        Args:
            u: Vértice de origem.
            v: Vértice de destino.

        Returns:
            Peso da aresta. Retorna 1.0 se a aresta existe mas peso não foi definido.

        Raises:
            ValueError: Se a aresta não existir.
        """

    @abstractmethod
    def getVertexInDegree(self, u: int) -> int:
        """
        Retorna o grau de entrada do vértice u.

        Grau de entrada = quantas arestas CHEGAM em u.
        Exemplo: se (a→u), (b→u), (c→u) existem → inDegree(u) = 3

        No projeto: indica quem recebe mais interações (mais "popular").

        Args:
            u: Índice do vértice.

        Returns:
            Número de arestas que chegam em u.
        """

    @abstractmethod
    def getVertexOutDegree(self, u: int) -> int:
        """
        Retorna o grau de saída do vértice u.

        Grau de saída = quantas arestas PARTEM de u.
        Exemplo: se (u→a), (u→b) existem → outDegree(u) = 2

        No projeto: indica quem mais interage com outros colaboradores.

        Args:
            u: Índice do vértice.

        Returns:
            Número de arestas que partem de u.
        """

    def isConnected(self) -> bool:
        """
        Verifica se o grafo é conexo (fortemente conexo para grafos direcionados).

        Grafo fortemente conexo: existe caminho de qualquer vértice para qualquer outro.
        Algoritmo típico: DFS/BFS a partir de um vértice, verificar se todos são alcançados,
        depois repetir no grafo transposto.

        Returns:
            True se o grafo for fortemente conexo.
        """
        if self._num_vertices <= 1:
            return True

        def bfs(source: int, use_transpose: bool = False) -> int:
            visited = [False] * self._num_vertices
            queue = deque([source])
            visited[source] = True
            count = 1

            while queue:
                current = queue.popleft()
                for neighbor in range(self._num_vertices):
                    if neighbor == current:
                        continue

                    has_edge = (
                        self.hasEdge(neighbor, current)
                        if use_transpose
                        else self.hasEdge(current, neighbor)
                    )
                    if has_edge and not visited[neighbor]:
                        visited[neighbor] = True
                        queue.append(neighbor)
                        count += 1

            return count

        total_vertices = self._num_vertices
        return bfs(0, use_transpose=False) == total_vertices and bfs(0, use_transpose=True) == total_vertices

    def isEmptyGraph(self) -> bool:
        """
        Verifica se o grafo é vazio (sem arestas).

        Grafo vazio: tem vértices mas nenhuma aresta.
        Diferente de grafo nulo (sem vértices) — aqui sempre há vértices.

        Returns:
            True se getEdgeCount() == 0.
        """
        return self.getEdgeCount() == 0

    def isCompleteGraph(self) -> bool:
        """
        Verifica se o grafo é completo.

        Grafo direcionado completo: existe aresta entre todo par ordenado (u, v)
        onde u != v. Para n vértices: n * (n-1) arestas no total.

        Exemplo: 3 vértices completo → 6 arestas:
            0→1, 0→2, 1→0, 1→2, 2→0, 2→1

        Returns:
            True se o número de arestas == n * (n - 1).
        """
        return self.getEdgeCount() == self._num_vertices * (self._num_vertices - 1)

    @abstractmethod
    def exportToGEPHI(self, path: str) -> None:
        """
        Exporta o grafo no formato GEXF para visualização no GEPHI.

        GEXF (Graph Exchange XML Format) é um dos formatos aceitos pelo GEPHI.
        O arquivo gerado pode ser aberto diretamente no software para visualização
        e análise visual da rede de colaboração.

        Referência: https://gephi.org/users/supported-graph-formats/

        Args:
            path: Caminho completo do arquivo de saída (ex: "grafo.gexf").
        """