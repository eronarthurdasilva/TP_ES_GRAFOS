"""
demo.py
=======
Demonstra todos os 25 métodos da API AbstractGraph.

Localização: raiz do projeto (TP_ES_GRAFOS/)

Rodar:
    cd TP_ES_GRAFOS
    python demo.py

Requisitos:
    pytest
"""

import sys
import os
import tempfile

# Ajusta path para encontrar os módulos
BASE_DIR = os.path.dirname(__file__)
ESTRUTURA_DIR = os.path.join(BASE_DIR, "Biblioteca", "EstruturadeClasses")
sys.path.insert(0, ESTRUTURA_DIR)

from AdjacencyMatrixGraph import AdjacencyMatrixGraph
from AdjacencyListGraph import AdjacencyListGraph


# ── Helpers de exibição ───────────────────────────────────────────────────────

def titulo(texto):
    print(f"\n{'='*55}")
    print(f"  {texto}")
    print('='*55)

def item(label, valor):
    print(f"  {label:<40} {valor}")


# ── Grafo de exemplo ──────────────────────────────────────────────────────────
#
#    Simula rede de colaboração com 5 devs:
#    0=vaxry  1=hypruser  2=contributor  3=reviewer  4=maintainer
#
#  Interações:
#    vaxry    → hypruser    (merge PR,    peso 5)
#    vaxry    → contributor (review,      peso 4)
#    hypruser → reviewer    (comentário,  peso 2)
#    hypruser → contributor (comentário,  peso 2)
#    reviewer → vaxry       (fechamento,  peso 3)
#    reviewer → vaxry       (comentário,  peso 2)  ← acumula → 5
#    maintainer → hypruser  (review,      peso 4)
#    maintainer → vaxry     (merge,       peso 5)

def construir_grafo_demo():
    g = AdjacencyMatrixGraph(5)

    interacoes = [
        (0, 1, 5.0),   # vaxry → hypruser    (merge)
        (0, 2, 4.0),   # vaxry → contributor (review)
        (1, 3, 2.0),   # hypruser → reviewer (comentário)
        (1, 2, 2.0),   # hypruser → contributor
        (3, 0, 3.0),   # reviewer → vaxry    (fechamento)
        (4, 1, 4.0),   # maintainer → hypruser
        (4, 0, 5.0),   # maintainer → vaxry
    ]

    for u, v, w in interacoes:
        g.setEdgeWeight(u, v, w)

    # Acumula reviewer→vaxry (comentário adicional)
    peso_atual = g.getEdgeWeight(3, 0)
    g.setEdgeWeight(3, 0, peso_atual + 2.0)   # 3 + 2 = 5.0

    logins = ["vaxry", "hypruser", "contributor", "reviewer", "maintainer"]
    for i, login in enumerate(logins):
        g.setVertexLabel(i, login)

    return g


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    # print("\n" + "█"*55)
    print("  DEMO — API AbstractGraph")
    print("  Projeto TP_ES_GRAFOS — Análise de Colaboração GitHub")
    # print("█"*55)

    g = construir_grafo_demo()


    # ── 1. Contagem ──────────────────────────────────────────────────────────
    titulo("1. CONTAGEM DE VÉRTICES E ARESTAS")
    item("getVertexCount()", g.getVertexCount())       # 5
    item("getEdgeCount()",   g.getEdgeCount())         # 7


    # ── 2. Rótulos e pesos de vértices ───────────────────────────────────────
    titulo("2. RÓTULOS E PESOS DE VÉRTICES")

    # setVertexLabel / getVertexLabel (já feito no construtor — mostra aqui)
    for i in range(g.getVertexCount()):
        item(f"getVertexLabel({i})", g.getVertexLabel(i))

    # setVertexWeight / getVertexWeight
    g.setVertexWeight(0, 99.5)
    item("setVertexWeight(0, 99.5) → getVertexWeight(0)", g.getVertexWeight(0))
    g.setVertexWeight(0, 0.0)   # reset


    # ── 3. Operações de aresta ────────────────────────────────────────────────
    titulo("3. OPERAÇÕES DE ARESTA")

    item("hasEdge(0, 1) — vaxry→hypruser",    g.hasEdge(0, 1))   # True
    item("hasEdge(1, 0) — inverso",           g.hasEdge(1, 0))   # False
    item("getEdgeWeight(0, 1)",               g.getEdgeWeight(0, 1))  # 5.0
    item("getEdgeWeight(3, 0) acumulado",     g.getEdgeWeight(3, 0))  # 5.0

    # addEdge → setEdgeWeight → removeEdge
    print("\n  [addEdge(2, 4)]")
    g.addEdge(2, 4)
    item("hasEdge(2, 4) após addEdge",        g.hasEdge(2, 4))   # True
    item("getEdgeCount() após addEdge",       g.getEdgeCount())  # 8

    g.setEdgeWeight(2, 4, 2.0)
    item("getEdgeWeight(2,4) após setWeight", g.getEdgeWeight(2, 4))  # 2.0

    print("\n  [removeEdge(2, 4)]")
    g.removeEdge(2, 4)
    item("hasEdge(2, 4) após removeEdge",     g.hasEdge(2, 4))   # False
    item("getEdgeCount() após removeEdge",    g.getEdgeCount())  # 7


    # ── 4. Graus ──────────────────────────────────────────────────────────────
    titulo("4. GRAUS DE ENTRADA E SAÍDA")

    for i in range(g.getVertexCount()):
        login  = g.getVertexLabel(i)
        in_d   = g.getVertexInDegree(i)
        out_d  = g.getVertexOutDegree(i)
        item(f"{login:<15} in={in_d}  out={out_d}", "")


    # ── 5. Relações entre vértices e arestas ──────────────────────────────────
    titulo("5. RELAÇÕES (herdados de AbstractGraph)")

    item("isSucessor(0, 1)   — 1 é sucessor de 0?",   g.isSucessor(0, 1))    # True
    item("isSucessor(1, 0)   — 0 é sucessor de 1?",   g.isSucessor(1, 0))    # False
    item("isPredecessor(0,1) — 0 precede 1?",          g.isPredecessor(0, 1)) # True

    # isDivergent: arestas com mesma origem
    item("isDivergent(0,1, 0,2) — 0→1 e 0→2 mesma origem?", g.isDivergent(0,1, 0,2))  # True
    item("isDivergent(0,1, 4,0) — origens diferentes?",      g.isDivergent(0,1, 4,0))  # False

    # isConvergent: arestas com mesmo destino
    item("isConvergent(0,1, 4,1) — destino 1 em comum?",    g.isConvergent(0,1, 4,1))  # True
    item("isConvergent(0,1, 0,2) — destinos diferentes?",   g.isConvergent(0,1, 0,2))  # False

    # isIncident: vértice faz parte da aresta?
    item("isIncident(0,1, 0) — 0 é origem de 0→1?",   g.isIncident(0,1, 0))  # True
    item("isIncident(0,1, 1) — 1 é destino de 0→1?",  g.isIncident(0,1, 1))  # True
    item("isIncident(0,1, 2) — 2 não está em 0→1?",   g.isIncident(0,1, 2))  # False


    # ── 6. Propriedades do grafo ──────────────────────────────────────────────
    titulo("6. PROPRIEDADES DO GRAFO")

    item("isEmptyGraph()    — tem arestas?",    g.isEmptyGraph())    # False
    item("isCompleteGraph() — todos conectados?", g.isCompleteGraph()) # False
    item("isConnected()     — fortemente conexo?", g.isConnected())  # depende

    # Demonstra isEmptyGraph com grafo vazio
    vazio = AdjacencyMatrixGraph(3)
    item("isEmptyGraph() em grafo novo",        vazio.isEmptyGraph())  # True

    # Demonstra isCompleteGraph com grafo completo
    completo = AdjacencyMatrixGraph(3)
    for u in range(3):
        for v in range(3):
            if u != v:
                completo.addEdge(u, v)
    item("isCompleteGraph() em grafo completo", completo.isCompleteGraph())  # True

    # Demonstra isConnected com ciclo
    ciclico = AdjacencyMatrixGraph(4)
    for u, v in [(0,1),(1,2),(2,3),(3,0)]:
        ciclico.addEdge(u, v)
    item("isConnected() com ciclo 0→1→2→3→0",  ciclico.isConnected())   # True


    # ── 7. Exportação GEXF ────────────────────────────────────────────────────
    titulo("7. EXPORTAÇÃO PARA GEPHI (.gexf)")

    with tempfile.NamedTemporaryFile(suffix=".gexf", delete=False, mode="w") as f:
        path_gexf = f.name

    g.exportToGEPHI(path_gexf)
    tamanho = os.path.getsize(path_gexf)
    item("Arquivo gerado",    path_gexf)
    item("Tamanho (bytes)",   tamanho)

    # Mostra primeiras linhas do GEXF
    print("\n  Primeiras 6 linhas do arquivo GEXF:")
    with open(path_gexf, encoding="utf-8") as f:
        for i, linha in enumerate(f):
            if i >= 6:
                break
            print(f"    {linha}", end="")

    os.unlink(path_gexf)


    # ── 8. Demonstração com AdjacencyListGraph ────────────────────────────────
    titulo("8. MESMO GRAFO COM LISTA DE ADJACÊNCIA")

    gl = AdjacencyListGraph(5)
    for u, v, w in [
        (0,1,5.0),(0,2,4.0),(1,3,2.0),(1,2,2.0),
        (3,0,5.0),(4,1,4.0),(4,0,5.0)
    ]:
        gl.setEdgeWeight(u, v, w)

    item("getVertexCount()", gl.getVertexCount())  # 5
    item("getEdgeCount()",   gl.getEdgeCount())    # 7
    item("hasEdge(0,1)",     gl.hasEdge(0,1))      # True
    item("getEdgeWeight(3,0)", gl.getEdgeWeight(3,0))  # 5.0


    # ── Resumo ────────────────────────────────────────────────────────────────
    titulo("RESUMO — MÉTODOS DEMONSTRADOS")
    metodos = [
        "getVertexCount", "getEdgeCount", "hasEdge", "addEdge", "removeEdge",
        "setEdgeWeight", "getEdgeWeight", "setVertexWeight", "getVertexWeight",
        "setVertexLabel", "getVertexLabel", "isSucessor", "isPredecessor",
        "isDivergent", "isConvergent", "isIncident", "getVertexInDegree",
        "getVertexOutDegree", "isConnected", "isEmptyGraph", "isCompleteGraph",
        "exportToGEPHI",
    ]
    for i, m in enumerate(metodos, 1):
        print(f"  {i:2}. {m}()")

    print(f"\n  Total: {len(metodos)} métodos demonstrados.")
    # print("\n" + "█"*55)
    print(" \n Demo concluído com sucesso.\n")
    # print("█"*55 + "\n")


if __name__ == "__main__":
    main()
