"""
test_construcao_grafos.py
=========================
Testa MapeamentoVertices e Construcao com JSONs temporários.

Não depende de dados reais do GitHub — cria fixtures em memória.

Localização esperada:
    TP_ES_GRAFOS/Biblioteca/ConstrucaoGrafos/test_construcao_grafos.py

Rodar:
    cd TP_ES_GRAFOS/Biblioteca/ConstrucaoGrafos
    python -m pytest test_construcao_grafos.py -v
    
Requisitos:
    pytest
"""

import sys
import os
import json
import tempfile
import shutil
import unittest
from pathlib import Path

# Ajusta paths para importar os módulos do projeto
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))
sys.path.insert(0, str(CURRENT_DIR.parent / "EstruturadeClasses"))

from MapeamentoVertices import MapeamentoVertices, gerar_mapeamento_vertices
from Construcao import Construcao


# ── Fixtures de dados ────────────────────────────────────────────────────────

COMENTARIOS = [
    {"de": "alice", "para": "bob",   "peso": 2},
    {"de": "alice", "para": "bob",   "peso": 2},   # duplicata → acumula
    {"de": "carol", "para": "alice", "peso": 2},
]

FECHAMENTOS = [
    {"de": "bob",   "para": "carol", "peso": 3},
]

REVIEWS = [
    {"de": "carol", "para": "bob",   "peso": 4},
    {"de": "alice", "para": "carol", "peso": 5},
]


def criar_dados_temp() -> Path:
    """Cria pasta temporária com os 3 JSONs de interação."""
    pasta = Path(tempfile.mkdtemp())
    (pasta / "comentarios.json").write_text(json.dumps(COMENTARIOS), encoding="utf-8")
    (pasta / "fechamentos.json").write_text(json.dumps(FECHAMENTOS), encoding="utf-8")
    (pasta / "reviews_merges.json").write_text(json.dumps(REVIEWS), encoding="utf-8")
    return pasta


# ── Testes de MapeamentoVertices ─────────────────────────────────────────────

class TestMapeamentoVertices(unittest.TestCase):

    def setUp(self):
        self.pasta = criar_dados_temp()
        self.mapeador = MapeamentoVertices(self.pasta)

    def tearDown(self):
        shutil.rmtree(self.pasta)

    def test_usuarios_unicos_coletados(self):
        mapa = self.mapeador.gerar()
        # 3 usuários únicos: alice, bob, carol
        self.assertEqual(len(mapa), 3)
        self.assertIn("alice", mapa)
        self.assertIn("bob",   mapa)
        self.assertIn("carol", mapa)

    def test_indices_sao_inteiros_unicos(self):
        mapa = self.mapeador.gerar()
        indices = list(mapa.values())
        # índices únicos
        self.assertEqual(len(indices), len(set(indices)))
        # índices inteiros sequenciais 0, 1, 2
        self.assertEqual(sorted(indices), list(range(3)))

    def test_mapa_ordenado_alfabeticamente(self):
        """Usuários devem ser mapeados em ordem alfabética (sorted)."""
        mapa = self.mapeador.gerar()
        usuarios_ordenados = sorted(mapa.keys())
        indices_em_ordem = [mapa[u] for u in usuarios_ordenados]
        self.assertEqual(indices_em_ordem, list(range(len(mapa))))

    def test_salva_json(self):
        arquivo = self.pasta / "mapeamento.json"
        resultado = self.mapeador.salvar(arquivo)
        self.assertTrue(arquivo.exists())
        # arquivo é JSON válido
        with arquivo.open() as f:
            dados = json.load(f)
        self.assertIn("global", dados)

    def test_gerar_por_arquivo(self):
        dados = self.mapeador.gerar_por_arquivo()
        self.assertIn("global", dados)
        self.assertIn("arquivos", dados)
        self.assertIn("alice", dados["global"]["mapeamento"])


# ── Testes de Construcao ──────────────────────────────────────────────────────

class TestConstrucao(unittest.TestCase):

    def setUp(self):
        self.pasta = criar_dados_temp()
        self.arquivo_mapeamento = self.pasta / "mapeamento.json"
        self.construtor = Construcao(
            dados_processados=self.pasta,
            arquivo_mapeamento=self.arquivo_mapeamento,
        )

    def tearDown(self):
        shutil.rmtree(self.pasta)

    # ── Número de vértices ────────────────────────────────────────────────────

    def test_quantidade_vertices_correta(self):
        grafo = self.construtor.construir_lista()
        # alice, bob, carol = 3 vértices
        self.assertEqual(grafo.getVertexCount(), 3)

    # ── Arestas existem ───────────────────────────────────────────────────────

    def test_arestas_criadas(self):
        grafo = self.construtor.construir_lista()
        # Deve ter arestas — não vazio
        self.assertGreater(grafo.getEdgeCount(), 0)

    # ── Pesos acumulados corretamente ─────────────────────────────────────────

    def test_peso_acumulado_alice_bob(self):
        """
        alice→bob aparece duas vezes em comentarios.json com peso 2 cada.
        Resultado esperado: peso total = 4.0
        """
        grafo = self.construtor.construir_lista()
        mapa = self._get_mapeamento()
        i_alice = mapa["alice"]
        i_bob   = mapa["bob"]

        self.assertTrue(grafo.hasEdge(i_alice, i_bob))
        self.assertEqual(grafo.getEdgeWeight(i_alice, i_bob), 4.0)

    def test_peso_fechamento(self):
        """bob→carol em fechamentos.json com peso 3."""
        grafo = self.construtor.construir_lista()
        mapa = self._get_mapeamento()
        self.assertTrue(grafo.hasEdge(mapa["bob"], mapa["carol"]))
        self.assertEqual(grafo.getEdgeWeight(mapa["bob"], mapa["carol"]), 3.0)

    def test_peso_review(self):
        """carol→bob em reviews_merges.json com peso 4."""
        grafo = self.construtor.construir_lista()
        mapa = self._get_mapeamento()
        self.assertTrue(grafo.hasEdge(mapa["carol"], mapa["bob"]))
        self.assertEqual(grafo.getEdgeWeight(mapa["carol"], mapa["bob"]), 4.0)

    # ── Sem duplicação de arestas ─────────────────────────────────────────────

    def test_sem_duplicacao_arestas(self):
        """
        Mesmo par (alice→bob) aparece duas vezes nos dados.
        Deve existir UMA aresta com peso acumulado, não duas.
        """
        grafo = self.construtor.construir_lista()
        mapa = self._get_mapeamento()
        i_alice = mapa["alice"]
        i_bob   = mapa["bob"]

        # Conta arestas saindo de alice para bob — deve ser exatamente 1
        count = sum(
            1 for v in range(grafo.getVertexCount())
            if v != i_alice and grafo.hasEdge(i_alice, v) and v == i_bob
        )
        self.assertEqual(count, 1)

    # ── Rótulos dos vértices ──────────────────────────────────────────────────

    def test_rotulos_atribuidos(self):
        """Cada vértice deve ter o login como rótulo."""
        grafo = self.construtor.construir_lista()
        mapa = self._get_mapeamento()
        for login, indice in mapa.items():
            self.assertEqual(grafo.getVertexLabel(indice), login)

    # ── Matriz produz mesmo resultado ─────────────────────────────────────────

    def test_matriz_igual_lista(self):
        """Matriz e lista devem produzir o mesmo número de arestas."""
        lista  = self.construtor.construir_lista()
        matriz = self.construtor.construir_matriz()
        self.assertEqual(lista.getEdgeCount(), matriz.getEdgeCount())
        self.assertEqual(lista.getVertexCount(), matriz.getVertexCount())

    # ── construir_todos retorna os dois ──────────────────────────────────────

    def test_construir_todos(self):
        from AdjacencyListGraph import AdjacencyListGraph
        from AdjacencyMatrixGraph import AdjacencyMatrixGraph
        lst, mat = self.construtor.construir_todos()
        self.assertIsInstance(lst, AdjacencyListGraph)
        self.assertIsInstance(mat, AdjacencyMatrixGraph)

    # ── Helper ───────────────────────────────────────────────────────────────

    def _get_mapeamento(self):
        """Lê o mapeamento gerado e retorna dict login→indice."""
        if not self.arquivo_mapeamento.exists():
            gerar_mapeamento_vertices(self.pasta, self.arquivo_mapeamento)
        with self.arquivo_mapeamento.open() as f:
            dados = json.load(f)
        return {k: int(v) for k, v in dados["global"]["mapeamento"].items()}


if __name__ == "__main__":
    unittest.main(verbosity=2)
