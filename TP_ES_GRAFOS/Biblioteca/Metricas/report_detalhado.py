#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Dict, Any


def load_json(path: Path) -> Any:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def load_vertex_labels(repo: str) -> Dict[str, str]:
    mapping_path = Path(__file__).resolve().parent.parent / 'ConstrucaoGrafos' / f'mapeamento_vertices_{repo}.json'
    if not mapping_path.exists():
        return {}
    data = load_json(mapping_path)
    mapping = data.get('global', {}).get('mapeamento', {})
    return {str(vertex_id): label for label, vertex_id in mapping.items()}


def print_top(mapping: Dict[str, float], name: str, labels: Dict[str, str], top: int = 10) -> None:
    print(f"\n{name} — Top {top}")
    items = sorted(mapping.items(), key=lambda kv: kv[1], reverse=True)[:top]
    for rank, (k, v) in enumerate(items, start=1):
        print(f"{rank:2d}. {labels.get(str(k), str(k))}: {v}")


def report_centrality(base: Path, graph_type: str, labels: Dict[str, str], top: int = 10) -> None:
    fname = f"grafo_{graph_type}_centralidade.json"
    path = base / 'centralidade' / fname
    if not path.exists():
        print(f"Centrality file not found: {path}")
        return
    data = load_json(path)
    print("\n=== Centralidade ===")
    # degree, betweenness, closeness, pagerank/eigen
    if 'degree_centrality' in data:
        print_top(data['degree_centrality'], 'Degree centrality', labels, top)
    if 'betweenness_centrality' in data:
        print_top(data['betweenness_centrality'], 'Betweenness centrality', labels, top)
    if 'closeness_centrality' in data:
        print_top(data['closeness_centrality'], 'Closeness centrality', labels, top)
    if 'pagerank' in data:
        print_top(data['pagerank'], 'PageRank', labels, top)
    elif 'eigenvector' in data:
        print_top(data['eigenvector'], 'Eigenvector centrality', labels, top)


def report_structure(base: Path) -> None:
    path = base / 'estrutura_coesao' / 'metricas_estrutura_coesao.json'
    if not path.exists():
        print(f"Estrutura file not found: {path}")
        return
    arr = load_json(path)
    print("\n=== Estrutura e Coesão ===")
    for g in arr:
        nome = g.get('nome_grafo', 'Grafo')
        densidade = g.get('densidade_nao_direcionada')
        clustering = g.get('coeficiente_aglomeracao_medio_todos_vertices')
        assort = g.get('assortatividade_por_grau')
        print(f"\n{nome}")
        print(f"  Densidade (não direcionada): {densidade}")
        print(f"  Coeficiente de aglomeração (médio): {clustering}")
        print(f"  Assortatividade por grau: {assort}")


def report_community(base: Path, graph_type: str, labels: Dict[str, str], top_coms: int = 10, top_bridges: int = 10) -> None:
    path = base / 'comunidade' / graph_type / 'metricas_comunidade.json'
    if not path.exists():
        print(f"Comunidade file not found: {path}")
        return
    data = load_json(path)
    print("\n=== Comunidade ===")
    print(f"Número de comunidades: {data.get('num_comunidades')}")
    print(f"Modularidade: {data.get('modularidade')}")
    comunidades = data.get('comunidades', [])
    comunidades_sorted = sorted(comunidades, key=lambda c: c.get('tamanho', 0), reverse=True)
    print(f"\nTop {top_coms} comunidades por tamanho:")
    for i, c in enumerate(comunidades_sorted[:top_coms], start=1):
        membros = c.get('membros', [])[:5]
        membros_traduzidos = [labels.get(str(m), str(m)) for m in membros]
        print(f"{i}. comunidade={c.get('id')} tamanho={c.get('tamanho')} membros={', '.join(membros_traduzidos)}")
    bridges = data.get('bridging_ties', [])
    if bridges:
        print(f"\nTop {top_bridges} bridging ties:")
        bridges_sorted = sorted(bridges, key=lambda b: (b.get('comunidades_vizinhas', 0), b.get('indice_intermediacao', 0)), reverse=True)
        for i, b in enumerate(bridges_sorted[:top_bridges], start=1):
            vertice = str(b.get('vertice'))
            print(f"{i}. vertice={labels.get(vertice, vertice)} comunidades_vizinhas={b.get('comunidades_vizinhas')} indice_intermediacao={b.get('indice_intermediacao')} grau={b.get('grau')}")


def main():
    parser = argparse.ArgumentParser(description='Relatório detalhado das métricas geradas')
    parser.add_argument('--repo', default='hyprland', help='Repositório (nome da pasta em saida_metricas)')
    parser.add_argument('--graph', choices=['lista', 'matriz'], default='lista', help='Tipo de grafo')
    parser.add_argument('--top', type=int, default=10, help='Top N para listagens')
    args = parser.parse_args()

    base = Path(__file__).resolve().parent / 'saida_metricas' / args.repo
    if not base.exists():
        print(f"Pasta de métricas não encontrada: {base}")
        return

    labels = load_vertex_labels(args.repo)

    report_centrality(base, args.graph, labels, top=args.top)
    report_structure(base)
    report_community(base, args.graph, labels, top_coms=args.top, top_bridges=args.top)


if __name__ == '__main__':
    main()
