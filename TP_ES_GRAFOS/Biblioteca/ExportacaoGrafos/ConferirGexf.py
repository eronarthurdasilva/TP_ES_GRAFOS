"""ConferirGexf.py
=================

Script simples para conferir se os arquivos .gexf têm nós e arestas.
Não usa biblioteca de grafos.

Como usar:
    python ConferirGexf.py saida_gexf_exemplo/grafo_4_integrado.gexf
"""

import sys
from pathlib import Path


def contar_ocorrencias(caminho):
    texto = Path(caminho).read_text(encoding="utf-8")

    # Conta apenas tags de nó/aresta individuais.
    # Evita contar <nodes> e <edges>.
    total_vertices = texto.count("<node ")
    total_arestas = texto.count("<edge ")

    print(f"Arquivo: {caminho}")
    print(f"Vértices encontrados: {total_vertices}")
    print(f"Arestas encontradas: {total_arestas}")

    if total_arestas == 0:
        print("Atenção: o arquivo está sem arestas.")
    else:
        print("OK: o arquivo possui arestas.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python ConferirGexf.py caminho_do_arquivo.gexf")
        sys.exit(1)

    contar_ocorrencias(sys.argv[1])
