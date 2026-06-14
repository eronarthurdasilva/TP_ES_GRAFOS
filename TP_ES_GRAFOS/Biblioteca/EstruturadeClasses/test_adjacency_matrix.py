"""
test_adjacency_matrix.py
========================
Testa AdjacencyMatrixGraph — todos os métodos da API.

Localização esperada:
    TP_ES_GRAFOS/Biblioteca/EstruturadeClasses/test_adjacency_matrix.py

Rodar:
    cd TP_ES_GRAFOS/Biblioteca/EstruturadeClasses
    python -m pytest test_adjacency_matrix.py -v

Requisitos:
    pytest
"""

import sys
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(__file__))

from AdjacencyMatrixGraph import AdjacencyMatrixGraph


class TestAdjacencyMatrixBasico(unittest.TestCase):
    """Operações básicas de aresta e vértice."""

    def setUp(self):
        self.g = AdjacencyMatrixGraph(4)

    # ── getVertexCount / getEdgeCount ─────────────────────────────────────────

    def test_vertex_count(self):
        self.assertEqual(self.g.getVertexCount(), 4)

    def test_edge_count_inicial(self):
        self.assertEqual(self.g.getEdgeCount(), 0)

    def test_edge_count_apos_add(self):
        self.g.addEdge(0, 1)
        self.g.addEdge(1, 2)
        self.assertEqual(self.g.getEdgeCount(), 2)

    # ── hasEdge ──────────────────────────────────────────────────────────────

    def test_has_edge_false_inicial(self):
        self.assertFalse(self.g.hasEdge(0, 1))

    def test_has_edge_true_apos_add(self):
        self.g.addEdge(0, 1)
        self.assertTrue(self.g.hasEdge(0, 1))

    def test_has_edge_direcionado(self):
        # 0→1 existe mas 1→0 não
        self.g.addEdge(0, 1)
        self.assertFalse(self.g.hasEdge(1, 0))

    def test_has_edge_vertice_invalido(self):
        with self.assertRaises((ValueError, IndexError)):
            self.g.hasEdge(0, 99)

    # ── addEdge ───────────────────────────────────────────────────────────────

    def test_add_edge_idempotente(self):
        """Chamar addEdge duas vezes não duplica a aresta."""
        self.g.addEdge(0, 1)
        self.g.addEdge(0, 1)
        self.assertEqual(self.g.getEdgeCount(), 1)

    def test_add_edge_laco_invalido(self):
        """Laço (u→u) deve ser rejeitado."""
        with self.assertRaises((ValueError, Exception)):
            self.g.addEdge(0, 0)

    # ── removeEdge ────────────────────────────────────────────────────────────

    def test_remove_edge_existente(self):
        self.g.addEdge(0, 1)
        self.g.removeEdge(0, 1)
        self.assertFalse(self.g.hasEdge(0, 1))
        self.assertEqual(self.g.getEdgeCount(), 0)

    def test_remove_edge_inexistente_lanca_erro(self):
        with self.assertRaises(ValueError):
            self.g.removeEdge(0, 1)

    # ── setEdgeWeight / getEdgeWeight ─────────────────────────────────────────

    def test_edge_weight_padrao(self):
        self.g.addEdge(0, 1)
        self.assertEqual(self.g.getEdgeWeight(0, 1), 1.0)

    def test_set_get_edge_weight(self):
        self.g.addEdge(0, 1)
        self.g.setEdgeWeight(0, 1, 5.0)
        self.assertEqual(self.g.getEdgeWeight(0, 1), 5.0)

    def test_set_edge_weight_cria_aresta(self):
        """setEdgeWeight em aresta inexistente deve criar a aresta."""
        self.g.setEdgeWeight(0, 1, 3.0)
        self.assertTrue(self.g.hasEdge(0, 1))
        self.assertEqual(self.g.getEdgeWeight(0, 1), 3.0)

    def test_get_edge_weight_inexistente_lanca_erro(self):
        with self.assertRaises((ValueError, Exception)):
            self.g.getEdgeWeight(0, 1)

    def test_edge_weight_zero_invalido(self):
        with self.assertRaises(ValueError):
            self.g.setEdgeWeight(0, 1, 0.0)

    # ── pesos do projeto (2, 3, 4, 5) ────────────────────────────────────────

    def test_pesos_do_projeto(self):
        pesos = [2.0, 3.0, 4.0, 5.0]
        arestas = [(0,1), (0,2), (1,2), (2,3)]
        for (u, v), w in zip(arestas, pesos):
            self.g.setEdgeWeight(u, v, w)
            self.assertEqual(self.g.getEdgeWeight(u, v), w)


class TestAdjacencyMatrixGraus(unittest.TestCase):
    """Testes de grau de entrada e saída."""

    def setUp(self):
        self.g = AdjacencyMatrixGraph(4)
        # 0→1, 0→2, 3→1
        self.g.addEdge(0, 1)
        self.g.addEdge(0, 2)
        self.g.addEdge(3, 1)

    def test_out_degree(self):
        self.assertEqual(self.g.getVertexOutDegree(0), 2)
        self.assertEqual(self.g.getVertexOutDegree(3), 1)
        self.assertEqual(self.g.getVertexOutDegree(1), 0)

    def test_in_degree(self):
        self.assertEqual(self.g.getVertexInDegree(1), 2)   # de 0 e de 3
        self.assertEqual(self.g.getVertexInDegree(2), 1)   # só de 0
        self.assertEqual(self.g.getVertexInDegree(0), 0)

    def test_grau_vertice_isolado(self):
        g = AdjacencyMatrixGraph(3)
        self.assertEqual(g.getVertexInDegree(0), 0)
        self.assertEqual(g.getVertexOutDegree(0), 0)


class TestAdjacencyMatrixPropriedades(unittest.TestCase):
    """isEmptyGraph, isCompleteGraph, isConnected."""

    def setUp(self):
        self.g = AdjacencyMatrixGraph(4)

    def test_is_empty_true(self):
        self.assertTrue(self.g.isEmptyGraph())

    def test_is_empty_false(self):
        self.g.addEdge(0, 1)
        self.assertFalse(self.g.isEmptyGraph())

    def test_is_complete_false(self):
        self.assertFalse(self.g.isCompleteGraph())

    def test_is_complete_true(self):
        n = 4
        for u in range(n):
            for v in range(n):
                if u != v:
                    self.g.addEdge(u, v)
        self.assertTrue(self.g.isCompleteGraph())

    def test_is_connected_ciclo(self):
        # 0→1→2→3→0 = fortemente conexo
        for u, v in [(0,1),(1,2),(2,3),(3,0)]:
            self.g.addEdge(u, v)
        self.assertTrue(self.g.isConnected())

    def test_is_connected_false(self):
        # apenas 0→1 — 2 e 3 não alcançam ninguém
        self.g.addEdge(0, 1)
        self.assertFalse(self.g.isConnected())

    def test_is_connected_grafo_vazio(self):
        # sem arestas não é fortemente conexo (com n>1)
        self.assertFalse(self.g.isConnected())


class TestAdjacencyMatrixExportacao(unittest.TestCase):
    """exportToGEPHI gera XML GEXF válido."""

    def setUp(self):
        self.g = AdjacencyMatrixGraph(3)
        self.g.addEdge(0, 1)
        self.g.setEdgeWeight(0, 1, 4.0)
        self.g.addEdge(1, 2)
        self.g.setVertexLabel(0, "alice")
        self.g.setVertexLabel(1, "bob")

    def test_exporta_sem_erro(self):
        with tempfile.NamedTemporaryFile(suffix=".gexf", delete=False) as f:
            path = f.name
        try:
            self.g.exportToGEPHI(path)
            self.assertTrue(os.path.exists(path))
        finally:
            os.unlink(path)

    def test_xml_valido(self):
        with tempfile.NamedTemporaryFile(suffix=".gexf", delete=False) as f:
            path = f.name
        try:
            self.g.exportToGEPHI(path)
            tree = ET.parse(path)   # lança ParseError se XML inválido
            root = tree.getroot()
            self.assertIn("gexf", root.tag)
        finally:
            os.unlink(path)

    def test_xml_tem_nos_e_arestas(self):
        with tempfile.NamedTemporaryFile(suffix=".gexf", delete=False) as f:
            path = f.name
        try:
            self.g.exportToGEPHI(path)
            tree = ET.parse(path)
            xml = ET.tostring(tree.getroot(), encoding="unicode")
            self.assertIn("alice", xml)
            self.assertIn("bob", xml)
            self.assertIn("4.0", xml)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
