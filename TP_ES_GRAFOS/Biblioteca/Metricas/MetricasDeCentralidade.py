
from collections import deque, defaultdict
from typing import Dict, List, Tuple
import math
 
 
class MetricasDeCentralidade:
    """
    Calcula 4 métricas de centralidade diferentes para um grafo direcionado.
    
    Funciona com qualquer implementação de AbstractGraph
    (AdjacencyMatrixGraph ou AdjacencyListGraph).
    """
 
    def __init__(self, grafo) -> None:
        """
        Inicializa a classe com um grafo.
 
        Args:
            grafo: Instância de AbstractGraph (ou subclasse)
                   Deve ter implementado: getVertexCount(), hasEdge(), 
                   getVertexInDegree(), getVertexOutDegree()
        """
        self.grafo = grafo
        self.n = grafo.getVertexCount()
 
    # ─────────────────────────────────────────────────────────────────────────
    # MÉTRICA 1: GRAU (DEGREE CENTRALITY)
    # ─────────────────────────────────────────────────────────────────────────
 
    def degree_centrality(self) -> Dict[int, float]:
        """
        Calcula a centralidade de grau de cada vértice.
 
        A centralidade de grau mede quantas conexões diretas cada colaborador tem.
        É a métrica mais simples e mais rápida de calcular.
 
        Fórmula:
            C_d(v) = deg(v) / (n - 1)
            onde deg(v) = número de arestas incidentes a v
            e n = número total de vértices
 
        Interpretação:
            - Valor entre 0 e 1
            - 1.0 = conectado a TODOS os outros vértices
            - 0.0 = isolado (nenhuma conexão)
            - No projeto: quem comenta/revisa mais frequentemente
 
        Retorna:
            Dicionário {vértice: centralidade}
            Ex: {0: 0.5, 1: 0.333, 2: 0.25, ...}
 
        Complexidade: O(n) — acessa grau de cada vértice
        """
        centrality = {}
 
        # Normalização: divisor é (n-1) porque não há auto-loops
        divisor = self.n - 1 if self.n > 1 else 1
 
        for v in range(self.n):
            # Grau total = entrada + saída (grafo direcionado)
            # No contexto de colaboração:
            #   - grau de entrada = quem interage COMIGO
            #   - grau de saída = EU INTERAGO com quem
            in_degree = self.grafo.getVertexInDegree(v)
            out_degree = self.grafo.getVertexOutDegree(v)
 
            # Soma os dois — mede "atividade total" do colaborador
            total_degree = in_degree + out_degree
 
            # Normaliza para [0, 1]
            centrality[v] = total_degree / divisor
 
        return centrality
 
    # ─────────────────────────────────────────────────────────────────────────
    # MÉTRICA 2: INTERMEDIAÇÃO (BETWEENNESS CENTRALITY)
    # ─────────────────────────────────────────────────────────────────────────
 
    def betweenness_centrality(self) -> Dict[int, float]:
        """
        Calcula a centralidade de intermediação de cada vértice.
 
        A betweenness identifica colaboradores que atuam como "pontes" —
        aqueles por quem muitos caminhos passam para ir de um grupo a outro.
 
        Fórmula:
            C_b(v) = Σ (σ_st(v) / σ_st) para todos s,t,v distintos
            onde:
                σ_st = número de caminhos mínimos de s a t
                σ_st(v) = número de caminhos mínimos de s a t que passam por v
 
        Interpretação:
            - Valor entre 0 e 1 (normalizado)
            - 1.0 = passa por todos os caminhos mínimos da rede
            - 0.0 = não está em nenhum caminho crítico
            - No projeto: quem conecta diferentes áreas/times do projeto
 
        Algoritmo:
            Brandes (2001) — BFS do Dijkstra para cada nó fonte
            1. Para cada s: fazer BFS
            2. Contar caminhos mínimos que chegam em cada t
            3. Backpropagate para contar quantos passam por cada v
 
        Retorna:
            Dicionário {vértice: betweenness}
 
        Complexidade: O(n * (n + m)) com BFS múltiplo
                      ≈ O(n³) para grafo denso
        """
        # Inicializa estruturas
        betweenness = {v: 0.0 for v in range(self.n)}
        
        # Para cada vértice como "fonte"
        for s in range(self.n):
            # ── BFS de s ──────────────────────────────────────────────────
            # Conta caminhos mínimos de s para todos os outros vértices
            
            pred = {v: [] for v in range(self.n)}  # predecessores no caminho mínimo
            sigma = {v: 0.0 for v in range(self.n)}  # número de caminhos mínimos
            sigma[s] = 1.0
            
            dist = {v: float('inf') for v in range(self.n)}
            dist[s] = 0
            
            queue = deque([s])
            stack = []  # para backpropagation
            
            # BFS para encontrar caminhos mínimos
            while queue:
                v = queue.popleft()
                stack.append(v)
                
                # Verifica todos os vizinhos de v
                for w in range(self.n):
                    if w == v:
                        continue

                    if self.grafo.hasEdge(v, w):
                        # Aresta v → w existe
                        
                        # Primeira vez que alcança w?
                        if dist[w] == float('inf'):
                            dist[w] = dist[v] + 1
                            queue.append(w)
                        
                        # É um caminho mínimo?
                        if dist[w] == dist[v] + 1:
                            sigma[w] += sigma[v]  # acumula caminhos
                            pred[w].append(v)      # v é predecessor no mínimo
            
            # ── Backpropagation ────────────────────────────────────────────
            # Conta quantas arestas ficam em caminhos mínimos entre s e t
            
            delta = {v: 0.0 for v in range(self.n)}
            
            # Processa em ordem reversa (do mais distante para o mais próximo)
            while stack:
                w = stack.pop()
                for v in pred[w]:
                    # Fração de caminhos de s→t que passam pela aresta v→w
                    delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
                
                if w != s:
                    betweenness[w] += delta[w]
        
        # Normaliza
        # Fator de normalização: cada par (s,t) é contado 2x em grafo direcionado
        if self.n > 2:
            norm_factor = 1.0 / ((self.n - 1) * (self.n - 2))
        else:
            norm_factor = 0.0
        
        for v in range(self.n):
            betweenness[v] *= norm_factor
        
        return betweenness
 
    # ─────────────────────────────────────────────────────────────────────────
    # MÉTRICA 3: PROXIMIDADE (CLOSENESS CENTRALITY)
    # ─────────────────────────────────────────────────────────────────────────
 
    def closeness_centrality(self) -> Dict[int, float]:
        """
        Calcula a centralidade de proximidade de cada vértice.
 
        A closeness mede quão "próximo" um colaborador está de todos os outros.
        Um nó com alta closeness tem acesso rápido (via caminhos curtos) à
        informação da rede.
 
        Fórmula:
            C_c(v) = (n - 1) / Σ d(v, t) para todos t != v
            onde d(v, t) = distância (comprimento do caminho mínimo)
 
        Interpretação:
            - Valor entre 0 e 1 (normalizado)
            - 1.0 = adjacente a todos os outros (distância média = 1)
            - 0.0 = isolado ou em componente separada
            - No projeto: quem tem acesso rápido a toda a comunidade
 
        Casos especiais:
            - Se o grafo não é conexo, alguns pares terão distância infinita
            - A fórmula é sensível a componentes desconectadas
            - Implementação só conta pares alcançáveis
 
        Retorna:
            Dicionário {vértice: closeness}
 
        Complexidade: O(n² + n*m) com BFS para cada vértice
        """
        closeness = {}
 
        for s in range(self.n):
            # ── BFS de s ────────────────────────────────────────────────
            # Calcula distância de s para todos os outros
 
            dist = {v: float('inf') for v in range(self.n)}
            dist[s] = 0
            
            queue = deque([s])
            reachable = 0  # conta quantos vértices são alcançáveis
            sum_distances = 0.0
 
            while queue:
                v = queue.popleft()
 
                for w in range(self.n):
                    if w == v:
                        continue

                    if self.grafo.hasEdge(v, w) and dist[w] == float('inf'):
                        dist[w] = dist[v] + 1
                        queue.append(w)
 
            # ── Acumula distâncias ────────────────────────────────────────
 
            for t in range(self.n):
                if t != s and dist[t] != float('inf'):
                    sum_distances += dist[t]
                    reachable += 1
 
            # ── Normaliza ──────────────────────────────────────────────────
 
            if reachable > 0 and sum_distances > 0:
                # Fórmula: (vértices alcançáveis) / (soma de distâncias)
                closeness[s] = reachable / sum_distances
            else:
                # Isolado ou em componente separada
                closeness[s] = 0.0
 
        return closeness
 
    # ─────────────────────────────────────────────────────────────────────────
    # MÉTRICA 4: PAGERANK / EIGENVECTOR CENTRALITY
    # ─────────────────────────────────────────────────────────────────────────
 
    def pagerank(self, damping_factor: float = 0.85, max_iter: int = 100,
                 tolerance: float = 1e-6) -> Dict[int, float]:
        """
        Calcula PageRank de cada vértice.
 
        PageRank mede a importância de um nó ponderando não só suas conexões
        diretas, mas também a importância dos nós que apontam para ele.
        Baseado no algoritmo do Google (Page et al., 1999).
 
        Fórmula iterativa:
            PR(v)^(t+1) = (1-d)/n + d * Σ (PR(u)^(t) / out_degree(u))
                                    para u que aponta para v
 
        Interpretação:
            - Valor entre 0 e 1
            - Colaboradores com PR alto são "influentes" na rede
            - Influência vem não só de conexões, mas de quem está conectado a você
            - No projeto: quem é referenciado por pessoas importantes?
 
        Parâmetros:
            damping_factor (float): probabilidade de "continuar" vs "pular" (0.85)
            max_iter (int): máximo de iterações (100)
            tolerance (float): critério de convergência (1e-6)
 
        Algoritmo:
            1. Inicializa todos os nós com PR = 1/n
            2. Iterativamente: calcula novo PR baseado nos vizinhos
            3. Para quando delta < tolerance ou atinge max_iter
            4. Normaliza para soma = 1
 
        Retorna:
            Dicionário {vértice: pagerank}
            Ex: {0: 0.35, 1: 0.25, 2: 0.15, ...}
 
        Complexidade: O(max_iter * m) onde m = número de arestas
                      Típico: 20-30 iterações para convergência
        """
        # ── Inicialização ──────────────────────────────────────────────────
        # Cada nó começa com probabilidade igual
 
        pr_current = {v: 1.0 / self.n for v in range(self.n)}
        pr_next = {v: 0.0 for v in range(self.n)}
 
        # ── Iterações ──────────────────────────────────────────────────────
 
        for iteration in range(max_iter):
            # Zera para acumular novos valores
            for v in range(self.n):
                pr_next[v] = (1 - damping_factor) / self.n
 
            # Para cada vértice de origem u
            for u in range(self.n):
                out_degree = self.grafo.getVertexOutDegree(u)
 
                # Se u não aponta para ninguém, distribui igualmente
                if out_degree == 0:
                    out_degree = self.n
 
                # Para cada vértice de destino v
                for v in range(self.n):
                    if v == u:
                        continue

                    if self.grafo.hasEdge(u, v):
                        # u aponta para v
                        # Contribui uma fração do PR de u
                        pr_next[v] += damping_factor * (pr_current[u] / out_degree)
 
            # ── Verificação de convergência ────────────────────────────────
 
            # Calcula a diferença máxima entre iterações
            delta = max(abs(pr_next[v] - pr_current[v]) for v in range(self.n))
 
            if delta < tolerance:
                # Convergiu
                break
 
            # Próxima iteração
            pr_current = pr_next.copy()
 
        # ── Normalização ───────────────────────────────────────────────────
        # Garante que suma = 1.0 (propriedade de probabilidade)
 
        total = sum(pr_current.values())
        if total > 0:
            pr_current = {v: pr_current[v] / total for v in range(self.n)}
 
        return pr_current
 
    # ─────────────────────────────────────────────────────────────────────────
    # MÉTODO AUXILIAR: IMPRIMIR RELATÓRIO
    # ─────────────────────────────────────────────────────────────────────────
 
    def relatorio_completo(self) -> str:
        """
        Gera um relatório textual com todas as 4 métricas calculadas.
 
        Retorna:
            String com tabela formatada das métricas
        """
        degree = self.degree_centrality()
        betweenness = self.betweenness_centrality()
        closeness = self.closeness_centrality()
        pagerank = self.pagerank()
 
        # Ordena por PageRank (decrescente)
        ranking = sorted(range(self.n), key=lambda v: pagerank[v], reverse=True)
 
        output = []
        output.append("\n" + "="*80)
        output.append("MÉTRICAS DE CENTRALIDADE DA REDE")
        output.append("="*80)
        output.append(f"{'Vértice':<10} {'Grau':<12} {'Intermediação':<15} {'Proximidade':<15} {'PageRank':<12}")
        output.append("-"*80)
 
        for v in ranking:
            output.append(
                f"{v:<10} {degree[v]:<12.4f} {betweenness[v]:<15.4f} "
                f"{closeness[v]:<15.4f} {pagerank[v]:<12.4f}"
            )
 
        output.append("="*80 + "\n")
        return "\n".join(output)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# EXEMPLO DE USO
# ─────────────────────────────────────────────────────────────────────────────
 
if __name__ == "__main__":
    # Exemplo simples com grafo de teste
    # (descomente para testar sem importar as classes completas)
    
    print("""
    EXEMPLO DE COMO USAR MetricasDeCentralidade:
    
    from EstruturadeClasses.AdjacencyMatrixGraph import AdjacencyMatrixGraph
    from Metricas.MetricasDeCentralidade import MetricasDeCentralidade
    
    # Cria um grafo
    g = AdjacencyMatrixGraph(5)
    g.addEdge(0, 1)
    g.addEdge(1, 2)
    g.addEdge(2, 3)
    g.addEdge(3, 4)
    g.addEdge(0, 4)
    
    # Calcula métricas
    metrics = MetricasDeCentralidade(g)
    degree = metrics.degree_centrality()
    betweenness = metrics.betweenness_centrality()
    closeness = metrics.closeness_centrality()
    pagerank = metrics.pagerank()
    
    # Printa relatório
    print(metrics.relatorio_completo())
    """)