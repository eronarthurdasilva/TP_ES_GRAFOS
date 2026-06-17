#!/usr/bin/env python3
"""Ponto de entrada principal do projeto.

Executa a coleta, o processamento e todas as métricas a partir da pasta
Biblioteca, com suporte aos repositórios h3 e hyprland.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import subprocess
import socket
import time
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

sys.path.insert(0, os.path.abspath(BASE_DIR / "ExtracaoDados"))
sys.path.insert(0, os.path.abspath(BASE_DIR / "ConstrucaoGrafos"))
sys.path.insert(0, os.path.abspath(BASE_DIR / "Metricas"))
sys.path.insert(0, os.path.abspath(BASE_DIR / "ExportacaoGrafos"))

from extracao_de_dados import ExtracaoDados
from config import (  # type: ignore[reportMissingImports]
    obter_config_repositorio,
    obter_caminho_mapeamento,
    obter_diretorios_dados,
)
from MapeamentoVertices import gerar_mapeamento_vertices  # type: ignore[reportMissingImports]
from Construcao import Construcao  # type: ignore[reportMissingImports]
from MetricasDeCentralidade import MetricasDeCentralidade  # type: ignore[reportMissingImports]
from MetricasDeComunidade import analisar_comunidades  # type: ignore[reportMissingImports]
from MetricasDeEstruturaCoesao import analisar_quatro_grafos_estrutura_coesao  # type: ignore[reportMissingImports]
from ExportacaoGexf import ExportacaoGexf  # type: ignore[reportMissingImports]
from gui_backend import executar_backend  # type: ignore[reportMissingImports]
from gui_views import mostrar_resultados  # type: ignore[reportMissingImports]


GUI_HOST = "127.0.0.1"
GUI_PORT = 8765


def _salvar_metricas_centralidade(grafo, nome_grafo: str, pasta_saida: Path) -> dict:
    """Calcula e salva as métricas de centralidade para um grafo já construído."""
    analisador = MetricasDeCentralidade(grafo)
    resultado = {
        "nome_grafo": nome_grafo,
        "degree_centrality": analisador.degree_centrality(),
        "betweenness_centrality": analisador.betweenness_centrality(),
        "closeness_centrality": analisador.closeness_centrality(),
        "pagerank": analisador.pagerank(),
        "relatorio": analisador.relatorio_completo(),
    }

    pasta_saida.mkdir(parents=True, exist_ok=True)
    arquivo_json = pasta_saida / f"{nome_grafo}_centralidade.json"
    arquivo_txt = pasta_saida / f"{nome_grafo}_centralidade.txt"

    with arquivo_json.open("w", encoding="utf-8") as arquivo:
        json.dump(resultado, arquivo, ensure_ascii=False, indent=2)

    with arquivo_txt.open("w", encoding="utf-8") as arquivo:
        arquivo.write(resultado["relatorio"])

    return resultado


def _executar_metricas(grafo_lista, grafo_matriz, repo_slug: str, dados_processados: Path) -> None:
    """Executa e persiste as três métricas do projeto após a construção dos grafos."""
    pasta_metricas = BASE_DIR / "Metricas" / "saida_metricas" / repo_slug

    comunidade_dir = pasta_metricas / "comunidade"
    centralidade_dir = pasta_metricas / "centralidade"
    estrutura_dir = pasta_metricas / "estrutura_coesao"

    resultado_comunidade_lista = analisar_comunidades(grafo_lista, comunidade_dir / "lista")
    resultado_comunidade_matriz = analisar_comunidades(grafo_matriz, comunidade_dir / "matriz")

    resultado_centralidade_lista = _salvar_metricas_centralidade(
        grafo_lista,
        "grafo_lista",
        centralidade_dir,
    )
    resultado_centralidade_matriz = _salvar_metricas_centralidade(
        grafo_matriz,
        "grafo_matriz",
        centralidade_dir,
    )

    resultados_estrutura = analisar_quatro_grafos_estrutura_coesao(
        pasta_dados_processados=dados_processados,
        pasta_saida=estrutura_dir,
    )

    print(
        "Metricas executadas com sucesso: "
        f"comunidade(lista={resultado_comunidade_lista['num_comunidades']}, "
        f"matriz={resultado_comunidade_matriz['num_comunidades']}), "
        f"centralidade(lista={len(resultado_centralidade_lista['pagerank'])}, "
        f"matriz={len(resultado_centralidade_matriz['pagerank'])}), "
        f"estrutura_coesao(grafos={len(resultados_estrutura)})"
    )


def _executar_exportacao(repo_slug: str, dados_processados: Path, mapeamento_saida: Path) -> None:
    """Executa a exportação GEXF e a exportação textual/CSV da interface do projeto."""
    pasta_saida_gexf = BASE_DIR / "ExportacaoGrafos" / "saida_gexf" / repo_slug
    pasta_saida_gui = BASE_DIR / "ExportacaoGrafos" / "saida_gui" / repo_slug

    print("Executando exportação GEXF...")
    exportador = ExportacaoGexf(
        dados_processados=dados_processados,
        arquivo_mapeamento=mapeamento_saida,
        pasta_saida=pasta_saida_gexf,
        exportar_vertices_isolados=False,
        ignorar_auto_lacos=True,
        normalizar_pesos_gephi=True,
        peso_visual_minimo=1.0,
        peso_visual_maximo=5.0,
    )
    exportador.exportar_todos()

    print("Executando interface textual e exportação complementar...")
    resultado_gui = executar_backend(
        pasta_dados_processados=dados_processados,
        pasta_saida=pasta_saida_gui,
        repo_slug=repo_slug,
    )
    mostrar_resultados(resultado_gui)


def _servidor_gui_ativo(host: str = GUI_HOST, port: int = GUI_PORT) -> bool:
    """Verifica se a interface web local ja esta escutando na porta padrao."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


def _abrir_gui_web(repo_slug: str, host: str = GUI_HOST, port: int = GUI_PORT) -> None:
    """Abre a interface web local no navegador apos executar o pipeline."""
    gui_script = BASE_DIR / "ExportacaoGrafos" / "gui_web.py"
    if not gui_script.exists():
        print(f"Interface web nao encontrada em {gui_script}")
        return

    url = f"http://{host}:{port}/?repo={repo_slug}"

    try:
        if not _servidor_gui_ativo(host, port):
            subprocess.Popen(
                [sys.executable, str(gui_script), "--host", host, "--port", str(port)],
                cwd=str(gui_script.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            time.sleep(0.8)

        print(f"Abrindo interface grafica em: {url}")
        webbrowser.open(url)
    except Exception as exc:  # pragma: no cover - depende do ambiente grafico local
        print(f"Nao foi possivel abrir a interface grafica automaticamente: {exc}")
        print(f"Abra manualmente: {url}")


def main(process_only: bool = False, force: bool = False, repo: str = "h3", exportar: bool = True):
    """Executa a extração, atualiza o mapeamento e devolve os dois grafos prontos."""
    config = obter_config_repositorio(repo)
    _dados_brutos, dados_processados = obter_diretorios_dados(repo)
    mapeamento_saida = obter_caminho_mapeamento(repo)

    print(f"Usando repositório: {config['owner']}/{config['repo']}")
    extrator = ExtracaoDados(repo)
    extrator.run(process_only=process_only, force=force)

    mapeamento = gerar_mapeamento_vertices(dados_processados, mapeamento_saida)
    total_global = len(mapeamento["global"]["mapeamento"])
    print(
        f"Mapeamento de vertices atualizado com {total_global} usuarios no mapa global em {mapeamento_saida}"
    )

    construtor = Construcao(dados_processados=dados_processados, arquivo_mapeamento=mapeamento_saida)
    start = time.perf_counter()
    grafo_lista, grafo_matriz = construtor.construir_todos()
    montagem_time = time.perf_counter() - start
    print(f"Tempo de montagem dos grafos: {montagem_time:.3f}s")

    _executar_metricas(grafo_lista, grafo_matriz, repo, dados_processados)

    if exportar:
        _executar_exportacao(repo, dados_processados, mapeamento_saida)

    # Gerar relatório detalhado automaticamente, se disponível
    try:
        report_script = BASE_DIR / "Metricas" / "report_detalhado.py"
        if report_script.exists():
            print("Gerando relatório detalhado das métricas...")
            for graph_type in ("lista", "matriz"):
                subprocess.run(
                    [sys.executable, str(report_script), "--repo", repo, "--graph", graph_type, "--top", "10"],
                    check=False,
                )
        else:
            print(f"Relatório detalhado não encontrado em {report_script}")
    except Exception as exc:  # pragma: no cover - best-effort reporting
        print(f"Falha ao gerar relatório detalhado: {exc}")

    return grafo_lista, grafo_matriz


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coleta e processa dados do GitHub")
    parser.add_argument(
        "--repo",
        "-r",
        choices=["h3", "hyprland"],
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
    parser.add_argument(
        "--sem-exportacao",
        action="store_true",
        help="Não executar a exportação GEXF nem a interface textual após montar os grafos.",
    )
    parser.add_argument(
        "--sem-gui",
        action="store_true",
        help="Não abrir a interface gráfica web ao final da execução.",
    )
    args = parser.parse_args()

    grafo_lista, grafo_matriz = main(
        process_only=args.process_only,
        force=args.force,
        repo=args.repo,
        exportar=not args.sem_exportacao,
    )
    print(
        f"Grafo em lista: {grafo_lista.getVertexCount()} vertices, {grafo_lista.getEdgeCount()} arestas"
    )
    print(
        f"Grafo em matriz: {grafo_matriz.getVertexCount()} vertices, {grafo_matriz.getEdgeCount()} arestas"
    )

    if not args.sem_gui and os.getenv("TP_ES_GRAFOS_SEM_GUI", "").lower() not in {"1", "true", "sim"}:
        _abrir_gui_web(args.repo)
