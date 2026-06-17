
"""ExportacaoGexf.py
===================

Exporta os 4 grafos do trabalho para GEXF, usando a etapa de construção
existente em ConstrucaoGrafos/Construcao.py.

Esta implementação altera apenas a camada de exportação. O Construcao.py não
precisa ser modificado.

Fluxo:
    dados_processados/*.json
        -> Construcao.py
        -> objeto de grafo em memória
        -> ExportacaoGexf.py
        -> arquivos .gexf para o Gephi

A implementação não usa bibliotecas de grafos, como NetworkX, igraph ou graph-tool.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Iterable, Dict, List, Tuple, Optional, Any


class ExportacaoGexf:
    """Classe responsável por exportar os grafos construídos para arquivos .gexf."""

    def __init__(
        self,
        dados_processados=None,
        arquivo_mapeamento=None,
        pasta_saida=None,
        exportar_vertices_isolados=False,
        ignorar_auto_lacos=True,
        normalizar_pesos_gephi=True,
        peso_visual_minimo=1.0,
        peso_visual_maximo=5.0,
    ):
        pasta_atual = Path(__file__).resolve().parent
        raiz_projeto = pasta_atual.parent

        self.dados_processados = (
            Path(dados_processados)
            if dados_processados
            else raiz_projeto / "ExtracaoDados" / "dados_processados"
        )
        self.arquivo_mapeamento = (
            Path(arquivo_mapeamento)
            if arquivo_mapeamento
            else self._descobrir_arquivo_mapeamento()
        )
        self.pasta_saida = Path(pasta_saida) if pasta_saida else pasta_atual / "saida_gexf"

        self.exportar_vertices_isolados = exportar_vertices_isolados
        self.ignorar_auto_lacos = ignorar_auto_lacos
        self.normalizar_pesos_gephi = normalizar_pesos_gephi
        self.peso_visual_minimo = float(peso_visual_minimo)
        self.peso_visual_maximo = float(peso_visual_maximo)

        self._classe_construcao_cache = None

    # ------------------------------------------------------------------
    # Localização e importação do Construcao.py
    # ------------------------------------------------------------------

    def _descobrir_arquivo_mapeamento(self):
        """Procura o arquivo de mapeamento em locais comuns do projeto."""
        pasta_atual = Path(__file__).resolve().parent
        raiz_projeto = pasta_atual.parent

        candidatos = [
            raiz_projeto / "ConstrucaoGrafos" / "mapeamento_vertices.json",
            pasta_atual / "mapeamento_vertices.json",
        ]

        for caminho in candidatos:
            if caminho.exists():
                return caminho

        return candidatos[0]

    def _descobrir_arquivo_construcao(self) -> Path:
        """
        Localiza o arquivo Construcao.py.

        O caminho principal esperado é:
            Projeto/Biblioteca/ConstrucaoGrafos/Construcao.py

        Como este arquivo fica em:
            Projeto/Biblioteca/ExportacaoGrafos/ExportacaoGexf.py

        basta subir uma pasta e procurar ConstrucaoGrafos/Construcao.py.
        """
        pasta_atual = Path(__file__).resolve().parent
        raiz_projeto = pasta_atual.parent

        candidatos = [
            raiz_projeto / "ConstrucaoGrafos" / "Construcao.py",
            Path.cwd() / "Biblioteca" / "ConstrucaoGrafos" / "Construcao.py",
            Path.cwd() / "ConstrucaoGrafos" / "Construcao.py",
        ]

        for caminho in candidatos:
            if caminho.exists():
                return caminho

        caminhos = "\n".join(str(c) for c in candidatos)
        raise FileNotFoundError(
            "Não foi possível localizar Construcao.py. Caminhos testados:\n"
            f"{caminhos}"
        )

    def _importar_classe_construcao(self):
        """
        Importa a classe Construcao diretamente pelo caminho do arquivo.

        Isso evita o erro:
            TypeError: NoneType takes no arguments

        Esse erro acontecia porque a classe Construcao não estava sendo importada
        corretamente e acabava ficando como None antes da herança.
        """
        if self._classe_construcao_cache is not None:
            return self._classe_construcao_cache

        caminho_construcao = self._descobrir_arquivo_construcao()
        pasta_construcao = caminho_construcao.parent
        raiz_projeto = pasta_construcao.parent
        pasta_estrutura = raiz_projeto / "EstruturadeClasses"

        # Garante que os imports usados dentro do próprio Construcao.py funcionem.
        for caminho in [pasta_construcao, pasta_estrutura]:
            caminho_str = str(caminho)
            if caminho_str not in sys.path:
                sys.path.insert(0, caminho_str)

        spec = importlib.util.spec_from_file_location("Construcao", caminho_construcao)
        if spec is None or spec.loader is None:
            raise ImportError(f"Não foi possível criar spec para: {caminho_construcao}")

        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)

        if not hasattr(modulo, "Construcao"):
            raise ImportError(f"O arquivo {caminho_construcao} não possui classe Construcao.")

        self._classe_construcao_cache = modulo.Construcao
        return self._classe_construcao_cache

    def _criar_construtor_filtrado(self, nomes_arquivos: List[str]):
        """
        Cria uma subclasse de Construcao sem modificar o arquivo original.

        A classe Construcao original sempre lê os três JSONs. Para exportar os
        quatro grafos separadamente, sobrescrevemos apenas _carregar_interacoes()
        dentro da exportação.
        """
        ClasseConstrucao = self._importar_classe_construcao()
        dados_processados = self.dados_processados
        arquivo_mapeamento = self.arquivo_mapeamento

        class ConstrucaoFiltrada(ClasseConstrucao):
            def __init__(self):
                super().__init__(
                    dados_processados=dados_processados,
                    arquivo_mapeamento=arquivo_mapeamento,
                )
                self._nomes_arquivos_exportacao = list(nomes_arquivos)

            def _carregar_interacoes(self):
                """Lê apenas os arquivos escolhidos pela exportação."""
                for nome in self._nomes_arquivos_exportacao:
                    arquivo = self.dados_processados / nome
                    if not arquivo.exists():
                        print(f"Aviso: arquivo não encontrado: {arquivo}")
                        continue

                    with arquivo.open("r", encoding="utf-8") as entrada:
                        dados = json.load(entrada)

                    if isinstance(dados, list):
                        for item in dados:
                            if isinstance(item, dict):
                                yield item

                    elif isinstance(dados, dict):
                        for chave in ("nodes", "items", "edges", "arestas", "interacoes"):
                            itens = dados.get(chave)
                            if isinstance(itens, list):
                                for item in itens:
                                    if isinstance(item, dict):
                                        yield item
                                break
                        else:
                            yield dados

        return ConstrucaoFiltrada()

    # ------------------------------------------------------------------
    # Utilitários de GEXF
    # ------------------------------------------------------------------

    def _escapar_xml(self, valor):
        """Escapa caracteres especiais para não quebrar o XML/GEXF."""
        texto = str(valor)
        texto = texto.replace("&", "&amp;")
        texto = texto.replace("<", "&lt;")
        texto = texto.replace(">", "&gt;")
        texto = texto.replace('"', "&quot;")
        texto = texto.replace("'", "&apos;")
        return texto

    def _normalizar_pesos_para_gephi(self, arestas: Dict[Tuple[int, int], float]):
        """
        Converte pesos reais em pesos visuais menores para o Gephi.

        O peso original continua preservado como atributo peso_original.
        """
        if not arestas:
            return {}

        if not self.normalizar_pesos_gephi:
            return {chave: peso for chave, peso in arestas.items()}

        pesos_log = {}
        menor = None
        maior = None

        for chave, peso in arestas.items():
            valor_log = math.log1p(max(0.0, float(peso)))
            pesos_log[chave] = valor_log

            if menor is None or valor_log < menor:
                menor = valor_log
            if maior is None or valor_log > maior:
                maior = valor_log

        pesos_visuais = {}
        intervalo_visual = self.peso_visual_maximo - self.peso_visual_minimo

        if maior == menor:
            for chave in pesos_log:
                pesos_visuais[chave] = self.peso_visual_minimo
            return pesos_visuais

        for chave, valor_log in pesos_log.items():
            proporcao = (valor_log - menor) / (maior - menor)
            peso_visual = self.peso_visual_minimo + (proporcao * intervalo_visual)
            pesos_visuais[chave] = round(peso_visual, 4)

        return pesos_visuais

    # ------------------------------------------------------------------
    # Extração dos dados do objeto de grafo construído
    # ------------------------------------------------------------------

    def _extrair_vertices_e_arestas_do_grafo(self, grafo):
        """
        Extrai vértices e arestas de um objeto criado pelo Construcao.py.

        Usa apenas a API comum do grafo:
            - getVertexCount()
            - getVertexLabel()
            - hasEdge()
            - getEdgeWeight()

        Assim funciona tanto com AdjacencyListGraph quanto com
        AdjacencyMatrixGraph.
        """
        quantidade_vertices = grafo.getVertexCount()
        vertices = {}
        arestas = {}
        vertices_usados = set()

        for origem in range(quantidade_vertices):
            for destino in range(quantidade_vertices):
                if self.ignorar_auto_lacos and origem == destino:
                    continue

                if grafo.hasEdge(origem, destino):
                    peso = float(grafo.getEdgeWeight(origem, destino))
                    chave = (origem, destino)
                    arestas[chave] = peso
                    vertices_usados.add(origem)
                    vertices_usados.add(destino)

        if self.exportar_vertices_isolados:
            indices_para_exportar = range(quantidade_vertices)
        else:
            indices_para_exportar = sorted(vertices_usados)

        for indice in indices_para_exportar:
            try:
                label = grafo.getVertexLabel(indice)
            except Exception:
                label = str(indice)

            if label is None or str(label).strip() == "":
                label = str(indice)

            vertices[indice] = str(label)

        return vertices, arestas

    def _construir_grafo_por_arquivos(self, arquivos: List[str]):
        """Constrói um grafo usando o Construcao.py filtrado pelos arquivos informados."""
        construtor = self._criar_construtor_filtrado(arquivos)
        return construtor.construir_lista()

    # ------------------------------------------------------------------
    # Escrita do GEXF
    # ------------------------------------------------------------------

    def _gerar_gexf(self, nome_grafo, vertices, arestas, tipo_relacao):
        """Gera o conteúdo textual do arquivo .gexf."""
        pesos_visuais = self._normalizar_pesos_para_gephi(arestas)

        linhas = []
        linhas.append('<?xml version="1.0" encoding="UTF-8"?>')
        linhas.append('<gexf xmlns="http://www.gexf.net/1.2draft" version="1.2">')
        linhas.append('  <meta>')
        linhas.append('    <creator>ExportacaoGrafos - usando Construcao.py</creator>')
        linhas.append(f'    <description>{self._escapar_xml(nome_grafo)}</description>')
        linhas.append('  </meta>')
        linhas.append('  <graph mode="static" defaultedgetype="directed">')

        linhas.append('    <attributes class="edge" mode="static">')
        linhas.append('      <attribute id="0" title="tipo_relacao" type="string" />')
        linhas.append('      <attribute id="1" title="peso_original" type="double" />')
        linhas.append('    </attributes>')

        linhas.append('    <nodes>')
        for indice in sorted(vertices.keys()):
            login = vertices[indice]
            linhas.append(
                f'      <node id="{self._escapar_xml(indice)}" label="{self._escapar_xml(login)}" />'
            )
        linhas.append('    </nodes>')

        linhas.append('    <edges>')
        id_aresta = 0

        for origem, destino in sorted(arestas.keys()):
            peso_original = arestas[(origem, destino)]
            peso_visual = pesos_visuais[(origem, destino)]

            linhas.append(
                f'      <edge id="{id_aresta}" '
                f'source="{self._escapar_xml(origem)}" '
                f'target="{self._escapar_xml(destino)}" '
                f'weight="{self._escapar_xml(peso_visual)}">'
            )
            linhas.append('        <attvalues>')
            linhas.append(
                f'          <attvalue for="0" value="{self._escapar_xml(tipo_relacao)}" />'
            )
            linhas.append(
                f'          <attvalue for="1" value="{self._escapar_xml(peso_original)}" />'
            )
            linhas.append('        </attvalues>')
            linhas.append('      </edge>')
            id_aresta += 1

        linhas.append('    </edges>')
        linhas.append('  </graph>')
        linhas.append('</gexf>')

        return "\n".join(linhas)

    def _salvar_gexf(self, nome_arquivo, conteudo):
        """Salva o arquivo GEXF na pasta de saída."""
        self.pasta_saida.mkdir(parents=True, exist_ok=True)
        caminho_saida = self.pasta_saida / nome_arquivo
        with caminho_saida.open("w", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)
        return caminho_saida

    # ------------------------------------------------------------------
    # Métodos públicos
    # ------------------------------------------------------------------

    def exportar_grafo_de_arquivos(self, arquivos, nome_arquivo_saida, nome_grafo, tipo_relacao):
        """Constrói um grafo com o Construcao.py e exporta para GEXF."""
        grafo = self._construir_grafo_por_arquivos(arquivos)
        vertices, arestas = self._extrair_vertices_e_arestas_do_grafo(grafo)

        if len(arestas) == 0:
            print(f"Aviso: grafo sem arestas para {nome_grafo}.")

        conteudo = self._gerar_gexf(nome_grafo, vertices, arestas, tipo_relacao)
        caminho = self._salvar_gexf(nome_arquivo_saida, conteudo)

        print(f"Exportado: {caminho} | vertices={len(vertices)} | arestas={len(arestas)}")
        return caminho

    def exportar_grafo_de_arquivo(self, nome_arquivo_json, nome_arquivo_saida, nome_grafo, tipo_relacao):
        """Mantém compatibilidade com chamadas antigas que exportam um único JSON."""
        return self.exportar_grafo_de_arquivos(
            arquivos=[nome_arquivo_json],
            nome_arquivo_saida=nome_arquivo_saida,
            nome_grafo=nome_grafo,
            tipo_relacao=tipo_relacao,
        )

    def exportar_grafo_integrado(self):
        """Exporta o grafo integrado, construído com os três arquivos de interações."""
        return self.exportar_grafo_de_arquivos(
            arquivos=["comentarios.json", "fechamentos.json", "reviews_merges.json"],
            nome_arquivo_saida="grafo_4_integrado.gexf",
            nome_grafo="Grafo 4 - Integrado",
            tipo_relacao="integrado",
        )

    def exportar_todos(self):
        """Exporta os quatro grafos esperados pelo trabalho."""
        saidas = []

        saidas.append(self.exportar_grafo_de_arquivo(
            nome_arquivo_json="comentarios.json",
            nome_arquivo_saida="grafo_1_comentarios.gexf",
            nome_grafo="Grafo 1 - Comentários em issues e PRs",
            tipo_relacao="comentario",
        ))

        saidas.append(self.exportar_grafo_de_arquivo(
            nome_arquivo_json="fechamentos.json",
            nome_arquivo_saida="grafo_2_fechamentos.gexf",
            nome_grafo="Grafo 2 - Fechamentos de issues",
            tipo_relacao="fechamento",
        ))

        saidas.append(self.exportar_grafo_de_arquivo(
            nome_arquivo_json="reviews_merges.json",
            nome_arquivo_saida="grafo_3_reviews_merges.gexf",
            nome_grafo="Grafo 3 - Reviews, aprovações e merges",
            tipo_relacao="review_merge",
        ))

        saidas.append(self.exportar_grafo_integrado())
        return saidas


def executar_por_linha_de_comando():
    parser = argparse.ArgumentParser(description="Exporta os 4 grafos do trabalho para GEXF/Gephi.")
    parser.add_argument("--dados", default=None, help="Caminho para dados_processados")
    parser.add_argument("--mapeamento", default=None, help="Caminho para mapeamento_vertices.json")
    parser.add_argument("--saida", default=None, help="Pasta de saída")
    parser.add_argument(
        "--com-isolados",
        action="store_true",
        help="Exporta também vértices sem arestas. Não recomendado para visualização inicial no Gephi.",
    )
    parser.add_argument(
        "--manter-auto-lacos",
        action="store_true",
        help="Mantém arestas em que origem e destino são o mesmo vértice.",
    )
    parser.add_argument(
        "--sem-normalizar-pesos",
        action="store_true",
        help="Usa o peso real no atributo weight. Pode deixar a visualização ruim no Gephi.",
    )
    parser.add_argument("--peso-min", type=float, default=1.0, help="Peso visual mínimo no Gephi")
    parser.add_argument("--peso-max", type=float, default=5.0, help="Peso visual máximo no Gephi")

    args = parser.parse_args()

    exportador = ExportacaoGexf(
        dados_processados=args.dados,
        arquivo_mapeamento=args.mapeamento,
        pasta_saida=args.saida,
        exportar_vertices_isolados=args.com_isolados,
        ignorar_auto_lacos=not args.manter_auto_lacos,
        normalizar_pesos_gephi=not args.sem_normalizar_pesos,
        peso_visual_minimo=args.peso_min,
        peso_visual_maximo=args.peso_max,
    )

    print("Dados processados:", exportador.dados_processados)
    print("Mapeamento:", exportador.arquivo_mapeamento)
    print("Pasta de saída:", exportador.pasta_saida)
    print("Exportar isolados:", exportador.exportar_vertices_isolados)
    print("Ignorar auto-laços:", exportador.ignorar_auto_lacos)
    print("Normalizar pesos para Gephi:", exportador.normalizar_pesos_gephi)
    print()

    exportador.exportar_todos()


if __name__ == "__main__":
    executar_por_linha_de_comando()
