#!/usr/bin/env python3
"""
Ponto de entrada para a extração de dados do repositório GitHub.
Executa a coleta de issues e pull requests.
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(Path(__file__).resolve().parent.parent / "ConstrucaoGrafos"))

from extracao_de_dados import ExtracaoDados
from MapeamentoVertices import gerar_mapeamento_vertices
from Construcao import Construcao

# Configurações dos repositórios disponíveis
REPOSITORIOS = {
    "h3": {"owner": "h3js", "repo": "h3"},
    "hyprland": {"owner": "hyprwm", "repo": "Hyprland"},
}

def main(process_only: bool = False, force: bool = False, repo: str = "h3"):
    """Executa a extração, atualiza o mapeamento e devolve os dois grafos prontos.
    
    Args:
        process_only: Se True, apenas processa JSONs existentes.
        force: Se True, força nova coleta mesmo se JSONs existem.
        repo: Nome do repositório ('h3' ou 'hyprland').
    """
    if repo not in REPOSITORIOS:
        raise ValueError(f"Repositório desconhecido: {repo}. Opções: {list(REPOSITORIOS.keys())}")
    
    config = REPOSITORIOS[repo]
    os.environ["GITHUB_OWNER"] = config["owner"]
    os.environ["GITHUB_REPO"] = config["repo"]
    
    base_dir = Path(__file__).resolve().parent
    dados_processados = base_dir / "dados_processados"
    mapeamento_saida = base_dir.parent / "ConstrucaoGrafos" / "mapeamento_vertices.json"

    print(f"Usando repositório: {config['owner']}/{config['repo']}")
    extrator = ExtracaoDados()
    extrator.run(process_only=process_only, force=force)

    mapeamento = gerar_mapeamento_vertices(dados_processados, mapeamento_saida)
    total_global = len(mapeamento["global"]["mapeamento"])
    print(
        f"Mapeamento de vertices atualizado com {total_global} usuarios no mapa global em {mapeamento_saida}"
    )

    construtor = Construcao(dados_processados=dados_processados, arquivo_mapeamento=mapeamento_saida)
    return construtor.construir_todos()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coleta e processa dados do GitHub")
    parser.add_argument(
        "--repo",
        "-r",
        choices=list(REPOSITORIOS.keys()),
        default="h3",
        help="Repositório a analisar (padrão: h3).",
    )
    parser.add_argument(
        "--process-only",
        "-p",
        action="store_true",
        help="Não faça a coleta; apenas processe JSONs brutos existentes (se houver).",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Forçar a coleta mesmo se existirem JSONs brutos locais.",
    )
    args = parser.parse_args()

    grafo_lista, grafo_matriz = main(process_only=args.process_only, force=args.force, repo=args.repo)
    print(
        f"Grafo em lista: {grafo_lista.getVertexCount()} vertices, {grafo_lista.getEdgeCount()} arestas"
    )
    print(
        f"Grafo em matriz: {grafo_matriz.getVertexCount()} vertices, {grafo_matriz.getEdgeCount()} arestas"
    )
