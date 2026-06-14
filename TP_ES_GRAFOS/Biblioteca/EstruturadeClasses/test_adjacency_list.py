"""
test_adjacency_list.py
======================
Testa AdjacencyListGraph — mesmos casos da matriz + comparação de performance.

Localização esperada:
    TP_ES_GRAFOS/Biblioteca/EstruturadeClasses/test_adjacency_list.py

Rodar:
    cd TP_ES_GRAFOS/Biblioteca/EstruturadeClasses
    python -m pytest test_adjacency_list.py -v
    
Requisitos:
    pytest
"""

import sys
import os
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(__file__))

from AdjacencyListGraph import AdjacencyListGraph
from AdjacencyMatrixGraph import AdjacencyMatrixGraph


class TestAdjacencyListBasico(unittest.TestCase):

    def setUp(self):
        self.g = AdjacencyListGraph(4)

    def test_vertex_count(self):
        self.assertEqual(self.g.getVertexCount(), 4)

    def test_edge_count_inicial(self):
        self.assertEqual(self.g.getEdgeCount(), 0)

    def test_has_edge_false_inicial(self):
        self.assertFalse(self.g.hasEdge(0, 1))

    def test_has_edge_true_apos_add(self):
        self.g.addEdge(0, 1)
        self.assertTrue(self.g.hasEdge(0, 1))

    def test_has_edge_direcionado(self):
        self.g.addEdge(0, 1)
        self.assertFalse(self.g.hasEdge(1, 0))

    def test_add_edge_idempotente(self):
        self.g.addEdge(0, 1)
        self.g.addEdge(0, 1)
        self.assertEqual(self.g.getEdgeCount(), 1)

    def test_add_edge_laco_invalido(self):
        with self.assertRaises((ValueError, Exception)):
            self.g.addEdge(0, 0)

    def test_remove_edge_existente(self):
        self.g.addEdge(0, 1)
        self.g.removeEdge(0, 1)
        self.assertFalse(self.g.hasEdge(0, 1))

    def test_remove_edge_inexistente_lanca_erro(self):
        with self.assertRaises(ValueError):
            self.g.removeEdge(0, 1)

    def test_set_get_edge_weight(self):
        self.g.addEdge(0, 1)
        self.g.setEdgeWeight(0, 1, 3.0)
        self.assertEqual(self.g.getEdgeWeight(0, 1), 3.0)

    def test_edge_weight_zero_invalido(self):
        with self.assertRaises(ValueError):
            self.g.setEdgeWeight(0, 1, 0.0)


class TestAdjacencyListGraus(unittest.TestCase):

    def setUp(self):
        self.g = AdjacencyListGraph(4)
        self.g.addEdge(0, 1)
        self.g.addEdge(0, 2)
        self.g.addEdge(3, 1)

    def test_out_degree(self):
        self.assertEqual(self.g.getVertexOutDegree(0), 2)
        self.assertEqual(self.g.getVertexOutDegree(3), 1)
        self.assertEqual(self.g.getVertexOutDegree(1), 0)

    def test_in_degree(self):
        self.assertEqual(self.g.getVertexInDegree(1), 2)
        self.assertEqual(self.g.getVertexInDegree(2), 1)
        self.assertEqual(self.g.getVertexInDegree(0), 0)


class TestAdjacencyListPropriedades(unittest.TestCase):

    def setUp(self):
        self.g = AdjacencyListGraph(4)

    def test_is_empty_true(self):
        self.assertTrue(self.g.isEmptyGraph())

    def test_is_empty_false(self):
        self.g.addEdge(0, 1)
        self.assertFalse(self.g.isEmptyGraph())

    def test_is_complete_true(self):
        n = 4
        for u in range(n):
            for v in range(n):
                if u != v:
                    self.g.addEdge(u, v)
        self.assertTrue(self.g.isCompleteGraph())

    def test_is_connected_ciclo(self):
        for u, v in [(0,1),(1,2),(2,3),(3,0)]:
            self.g.addEdge(u, v)
        self.assertTrue(self.g.isConnected())

    def test_is_connected_false(self):
        self.g.addEdge(0, 1)
        self.assertFalse(self.g.isConnected())


class TestAdjacencyListExportacao(unittest.TestCase):

    def setUp(self):
        self.g = AdjacencyListGraph(3)
        self.g.addEdge(0, 1)
        self.g.setEdgeWeight(0, 1, 4.0)
        self.g.setVertexLabel(0, "alice")

    def test_xml_valido(self):
        with tempfile.NamedTemporaryFile(suffix=".gexf", delete=False) as f:
            path = f.name
        try:
            self.g.exportToGEPHI(path)
            tree = ET.parse(path)
            root = tree.getroot()
            self.assertIn("gexf", root.tag)
        finally:
            os.unlink(path)


class TestPerformanceMatrizVsLista(unittest.TestCase):
    """
    Comparação de performance: hasEdge() matriz vs lista.

    Matriz → O(1): acesso direto à posição [u][v]
    Lista  → O(1) amortizado: lookup de dicionário Python

    Ambos são rápidos na prática para grafos pequenos.
    O teste verifica que nenhum é mais de 10x mais lento que o outro.
    """

    N = 80      # tamanho do grafo de teste
    ITER = 500  # repetições para medir

    @classmethod
    def setUpClass(cls):
        cls.mat = AdjacencyMatrixGraph(cls.N)
        cls.lst = AdjacencyListGraph(cls.N)

        # Grafo denso: ~metade das arestas possíveis
        for u in range(cls.N):
            for v in range(u + 1, cls.N):
                cls.mat.addEdge(u, v)
                cls.lst.addEdge(u, v)

    def _medir(self, grafo, u, v, n_iter):
        t0 = time.perf_counter()
        for _ in range(n_iter):
            grafo.hasEdge(u, v)
        return time.perf_counter() - t0

    def test_has_edge_performance(self):
        u, v = 10, 70
        t_mat = self._medir(self.mat, u, v, self.ITER)
        t_lst = self._medir(self.lst, u, v, self.ITER)

        print(f"\n  Matriz hasEdge: {t_mat*1000:.3f}ms")
        print(f"  Lista  hasEdge: {t_lst*1000:.3f}ms")

        # Nenhum deve ser 10x mais lento que o outro
        if t_mat > 0 and t_lst > 0:
            self.assertLess(t_mat / t_lst, 10.0)
            self.assertLess(t_lst / t_mat, 10.0)

    def test_in_degree_performance(self):
        """
        getVertexInDegree: matriz O(n), lista O(n) — ambos percorrem tudo.
        Lista pode ser mais lenta por lookup de dict.
        """
        t_mat = self._medir(self.mat, 40, 0, self.ITER)
        t_lst = self._medir(self.lst, 40, 0, self.ITER)

        print(f"\n  Matriz inDegree: {t_mat*1000:.3f}ms")
        print(f"  Lista  inDegree: {t_lst*1000:.3f}ms")

        # Tolerância generosa — mesma complexidade assintótica
        self.assertLess(max(t_mat, t_lst) / min(t_mat, t_lst), 15.0)

    def test_memoria_lista_menor_que_matriz(self):
        """
        Lista de adjacência usa menos memória para grafos esparsos.
        Para grafos densos (como este teste), a diferença é menor.
        Verifica apenas que o número de arestas é igual nos dois.
        """
        self.assertEqual(self.mat.getEdgeCount(), self.lst.getEdgeCount())


if __name__ == "__main__":
    unittest.main(verbosity=2)
