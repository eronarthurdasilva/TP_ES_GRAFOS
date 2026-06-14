"""
test_abstract_graph.py
======================
Testa a classe abstrata AbstractGraph e os métodos concretos herdados.

Localização esperada:
    TP_ES_GRAFOS/Biblioteca/EstruturadeClasses/test_abstract_graph.py

Rodar:
    cd TP_ES_GRAFOS/Biblioteca/EstruturadeClasses
    python -m pytest test_abstract_graph.py -v

Requisitos:
    pytest
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from AbstractGraph import AbstractGraph
from AdjacencyMatrixGraph import AdjacencyMatrixGraph


class TestAbstractGraph(unittest.TestCase):

    # ── Instanciação direta deve falhar ──────────────────────────────────────

    def test_nao_pode_instanciar_diretamente(self):
        """AbstractGraph é abstrata — instanciar lança TypeError."""
        with self.assertRaises(TypeError):
            AbstractGraph(4)

    # ── Métodos concretos herdados — testados via AdjacencyMatrixGraph ───────

    def setUp(self):
        self.g = AdjacencyMatrixGraph(4)
        self.g.addEdge(0, 1)   # aresta base para os testes relacionais
        self.g.addEdge(0, 2)   # segunda aresta saindo de 0 (divergente com 0→1)
        self.g.addEdge(3, 1)   # aresta convergente com 0→1 (destino = 1)

    # ── setVertexWeight / getVertexWeight ─────────────────────────────────────

    def test_vertex_weight_default_zero(self):
        self.assertEqual(self.g.getVertexWeight(0), 0.0)

    def test_set_get_vertex_weight(self):
        self.g.setVertexWeight(0, 42.0)
        self.assertEqual(self.g.getVertexWeight(0), 42.0)

    def test_vertex_weight_vertice_invalido(self):
        with self.assertRaises((ValueError, IndexError)):
            self.g.getVertexWeight(99)

    # ── setVertexLabel / getVertexLabel ──────────────────────────────────────

    def test_vertex_label_default_vazio(self):
        self.assertEqual(self.g.getVertexLabel(0), '')

    def test_set_get_vertex_label(self):
        self.g.setVertexLabel(0, "vaxry")
        self.assertEqual(self.g.getVertexLabel(0), "vaxry")

    # ── isSucessor ───────────────────────────────────────────────────────────

    def test_is_sucessor_true(self):
        # 0→1 existe: 1 é sucessor de 0
        self.assertTrue(self.g.isSucessor(0, 1))

    def test_is_sucessor_false(self):
        # 1→0 não existe
        self.assertFalse(self.g.isSucessor(1, 0))

    # ── isPredecessor ─────────────────────────────────────────────────────────

    def test_is_predecessor_true(self):
        # 0→1 existe: 0 é predecessor de 1
        self.assertTrue(self.g.isPredecessor(0, 1))

    def test_is_predecessor_false(self):
        self.assertFalse(self.g.isPredecessor(1, 0))

    def test_predecessor_equals_sucessor(self):
        # isPredecessor(u,v) == isSucessor(u,v) — semântica diferente, mesmo resultado
        self.assertEqual(
            self.g.isPredecessor(0, 1),
            self.g.isSucessor(0, 1)
        )

    # ── isDivergent ──────────────────────────────────────────────────────────

    def test_is_divergent_true(self):
        # 0→1 e 0→2 partem de 0 → divergentes
        self.assertTrue(self.g.isDivergent(0, 1, 0, 2))

    def test_is_divergent_false(self):
        # 0→1 e 3→1 partem de origens diferentes → não divergentes
        self.assertFalse(self.g.isDivergent(0, 1, 3, 1))

    # ── isConvergent ─────────────────────────────────────────────────────────

    def test_is_convergent_true(self):
        # 0→1 e 3→1 chegam em 1 → convergentes
        self.assertTrue(self.g.isConvergent(0, 1, 3, 1))

    def test_is_convergent_false(self):
        # 0→1 e 0→2 chegam em destinos diferentes → não convergentes
        self.assertFalse(self.g.isConvergent(0, 1, 0, 2))

    # ── isIncident ───────────────────────────────────────────────────────────

    def test_is_incident_origem(self):
        # 0 é origem de 0→1 → incidente
        self.assertTrue(self.g.isIncident(0, 1, 0))

    def test_is_incident_destino(self):
        # 1 é destino de 0→1 → incidente
        self.assertTrue(self.g.isIncident(0, 1, 1))

    def test_is_incident_false(self):
        # 2 não faz parte da aresta 0→1
        self.assertFalse(self.g.isIncident(0, 1, 2))


if __name__ == "__main__":
    unittest.main(verbosity=2)
