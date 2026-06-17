"""ExportacaoGexf.py
===================

Exporta os 4 grafos do trabalho para GEXF, usando o Construcao.py existente.

Para cada um dos 4 grafos esperados, são gerados dois arquivos .gexf:

    - um a partir do AdjacencyListGraph
    - um a partir do AdjacencyMatrixGraph

Total gerado:
    4 grafos x 2 representações = 8 arquivos .gexf

Ajustes para visualização no Gephi:
    - por padrão, exporta apenas vértices que possuem arestas;
    - por padrão, ignora auto-laços;
    - por padrão, normaliza o peso visual no atributo weight;
    - preserva o peso real no atributo peso_original.

Não usa bibliotecas de grafos como NetworkX, igraph ou graph-tool.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Any


# ==========================================================
# IMPORTAÇÃO SEGURA DO CONSTRUTOR
# ==========================================================


def _localizar_construcao_py() -> Path:
    """
    Localiza o arquivo Construcao.py em estruturas comuns do projeto.

    A estrutura principal esperada é:

        Biblioteca/
        ├── ConstrucaoGrafos/
        │   └── Construcao.py
        └── ExportacaoGrafos/
            └── ExportacaoGexf.py

    Também há candidatos extras para reduzir erro de caminho quando o script
    for chamado a partir da raiz do repositório.
    """
    pasta_atual = Path(__file__).resolve().parent

    candidatos = [
        pasta_atual.parent / "ConstrucaoGrafos" / "Construcao.py",
        pasta_atual.parent.parent / "ConstrucaoGrafos" / "Construcao.py",
        pasta_atual.parent / "Biblioteca" / "ConstrucaoGrafos" / "Construcao.py",
        pasta_atual.parent.parent / "Biblioteca" / "ConstrucaoGrafos" / "Construcao.py",
    ]

    for candidato in candidatos:
        if candidato.exists():
            return candidato

    mensagem = ["Não foi possível localizar Construcao.py.", "Caminhos testados:"]
    for candidato in candidatos:
        mensagem.append(f"- {candidato}")
    raise FileNotFoundError("\n".join(mensagem))


def _importar_classe_construcao():
    """
    Importa a classe Construcao diretamente do arquivo Construcao.py.

    Isso evita problemas de importação quando o script é executado por caminhos
    relativos diferentes no terminal.
    """
    caminho_construcao = _localizar_construcao_py()
    pasta_construcao = caminho_construcao.parent
    pasta_biblioteca = pasta_construcao.parent
    pasta_estrutura = pasta_biblioteca / "EstruturadeClasses"

    # O Construcao.py depende de módulos da própria pasta e de EstruturadeClasses.
    for caminho in [pasta_construcao, pasta_estrutura, pasta_biblioteca]:
        texto = str(caminho)
        if texto not in sys.path:
            sys.path.insert(0, texto)

    spec = importlib.util.spec_from_file_location("Construcao", caminho_construcao)
    if spec is None or spec.loader is None:
        raise ImportError(f"Não foi possível criar spec de importação para: {caminho_construcao}")

    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    if not hasattr(modulo, "Construcao"):
        raise ImportError(f"O arquivo não possui uma classe chamada Construcao: {caminho_construcao}")

    return modulo.Construcao


ConstrucaoBase = _importar_classe_construcao()


class ConstrucaoFiltrada(ConstrucaoBase):
    """
    Especialização da classe Construcao usada apenas pela exportação.

    O Construcao.py original sempre lê os três arquivos:
        - comentarios.json
        - fechamentos.json
        - reviews_merges.json

    Para exportar os 4 grafos separadamente, esta classe sobrescreve apenas o
    método _carregar_interacoes(), permitindo escolher quais arquivos entram na
    construção. O restante da construção continua usando o código original.
    """

    def __init__(self, nomes_arquivos: List[str], dados_processados=None, arquivo_mapeamento=None) -> None:
        super().__init__(dados_processados=dados_processados, arquivo_mapeamento=arquivo_mapeamento)
        self.nomes_arquivos = nomes_arquivos

    def _carregar_interacoes(self) -> Iterable[Dict[str, object]]:
        """
        Lê somente os JSONs definidos em self.nomes_arquivos.

        Este método segue a mesma estrutura do Construcao.py original, mas com
        a lista de arquivos parametrizada.
        """
        for nome in self.nomes_arquivos:
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
                for chave in ("nodes", "items"):
                    itens = dados.get(chave)
                    if isinstance(itens, list):
                        for item in itens:
                            if isinstance(item, dict):
                                yield item
                        break
                else:
                    yield dados


# ==========================================================
# EXPORTAÇÃO GEXF
# ==========================================================


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

        self.dados_processados = Path(dados_processados) if dados_processados else raiz_projeto / "ExtracaoDados" / "dados_processados"
        self.arquivo_mapeamento = Path(arquivo_mapeamento) if arquivo_mapeamento else self._descobrir_arquivo_mapeamento()
        self.pasta_saida = Path(pasta_saida) if pasta_saida else pasta_atual / "saida_gexf"

        self.exportar_vertices_isolados = exportar_vertices_isolados
        self.ignorar_auto_lacos = ignorar_auto_lacos
        self.normalizar_pesos_gephi = normalizar_pesos_gephi
        self.peso_visual_minimo = float(peso_visual_minimo)
        self.peso_visual_maximo = float(peso_visual_maximo)

    # ------------------------------------------------------
    # Caminhos e utilidades
    # ------------------------------------------------------

    def _descobrir_arquivo_mapeamento(self) -> Path:
        """Procura o arquivo mapeamento_vertices.json em locais comuns."""
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

    def _escapar_xml(self, valor: Any) -> str:
        """Escapa caracteres especiais para evitar quebra do XML/GEXF."""
        texto = str(valor)
        texto = texto.replace("&", "&amp;")
        texto = texto.replace("<", "&lt;")
        texto = texto.replace(">", "&gt;")
        texto = texto.replace('"', "&quot;")
        texto = texto.replace("'", "&apos;")
        return texto

    def _obter_label_vertice(self, grafo, indice: int) -> str:
        """Obtém o label do vértice usando a API pública ou o atributo interno."""
        try:
            label = grafo.getVertexLabel(indice)
            if label is not None and str(label).strip() != "":
                return str(label)
        except Exception:
            pass

        try:
            labels = getattr(grafo, "_vertex_labels")
            label = labels[indice]
            if label is not None and str(label).strip() != "":
                return str(label)
        except Exception:
            pass

        return str(indice)

    # ------------------------------------------------------
    # Leitura das arestas a partir dos objetos de grafo
    # ------------------------------------------------------

    def _extrair_arestas_do_grafo(self, grafo) -> Dict[Tuple[int, int], float]:
        """
        Extrai arestas de um objeto AdjacencyListGraph ou AdjacencyMatrixGraph.

        Retorno:
            {(origem, destino): peso}

        Observação:
        - Se o grafo possuir _adjacency_list, usa a estrutura de lista.
        - Se possuir _matrix, usa a estrutura de matriz.
        - Caso contrário, usa a API genérica hasEdge/getEdgeWeight.
        """
        arestas: Dict[Tuple[int, int], float] = {}

        if hasattr(grafo, "_adjacency_list"):
            adjacency_list = getattr(grafo, "_adjacency_list")

            for origem, vizinhos in adjacency_list.items():
                for destino, peso in vizinhos.items():
                    if self.ignorar_auto_lacos and origem == destino:
                        continue
                    arestas[(int(origem), int(destino))] = float(peso)

            return arestas

        if hasattr(grafo, "_matrix"):
            matriz = getattr(grafo, "_matrix")

            for origem in range(len(matriz)):
                for destino in range(len(matriz[origem])):
                    peso = matriz[origem][destino]
                    if peso != 0.0:
                        if self.ignorar_auto_lacos and origem == destino:
                            continue
                        arestas[(int(origem), int(destino))] = float(peso)

            return arestas

        # Fallback genérico, caso surja uma implementação nova de grafo.
        quantidade_vertices = grafo.getVertexCount()
        for origem in range(quantidade_vertices):
            for destino in range(quantidade_vertices):
                if self.ignorar_auto_lacos and origem == destino:
                    continue

                try:
                    if grafo.hasEdge(origem, destino):
                        arestas[(origem, destino)] = float(grafo.getEdgeWeight(origem, destino))
                except Exception:
                    continue

        return arestas

    def _obter_vertices_para_exportacao(self, grafo, arestas: Dict[Tuple[int, int], float]) -> Dict[int, str]:
        """Define quais vértices serão escritos no GEXF."""
        quantidade_vertices = grafo.getVertexCount()

        if self.exportar_vertices_isolados:
            return {
                indice: self._obter_label_vertice(grafo, indice)
                for indice in range(quantidade_vertices)
            }

        vertices_usados = set()
        for origem, destino in arestas.keys():
            vertices_usados.add(origem)
            vertices_usados.add(destino)

        return {
            indice: self._obter_label_vertice(grafo, indice)
            for indice in sorted(vertices_usados)
        }

    # ------------------------------------------------------
    # Pesos para visualização no Gephi
    # ------------------------------------------------------

    def _normalizar_pesos_para_gephi(self, arestas: Dict[Tuple[int, int], float]) -> Dict[Tuple[int, int], float]:
        """
        Converte pesos reais em pesos visuais menores.

        O peso original fica preservado no atributo peso_original. O atributo
        weight recebe o peso normalizado para melhorar a visualização no Gephi.
        """
        if not arestas:
            return {}

        if not self.normalizar_pesos_gephi:
            return {chave: float(peso) for chave, peso in arestas.items()}

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

        if menor is None or maior is None:
            return {}

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

    # ------------------------------------------------------
    # Geração do GEXF
    # ------------------------------------------------------

    def _gerar_gexf(self, nome_grafo: str, representacao: str, vertices: Dict[int, str], arestas: Dict[Tuple[int, int], float], tipo_relacao: str) -> str:
        """Gera o conteúdo textual do arquivo .gexf."""
        pesos_visuais = self._normalizar_pesos_para_gephi(arestas)

        linhas = []
        linhas.append('<?xml version="1.0" encoding="UTF-8"?>')
        linhas.append('<gexf xmlns="http://www.gexf.net/1.2draft" version="1.2">')
        linhas.append('  <meta>')
        linhas.append('    <creator>ExportacaoGrafos - usando Construcao.construir_todos()</creator>')
        linhas.append(f'    <description>{self._escapar_xml(nome_grafo)} - {self._escapar_xml(representacao)}</description>')
        linhas.append('  </meta>')
        linhas.append('  <graph mode="static" defaultedgetype="directed">')

        linhas.append('    <attributes class="graph" mode="static">')
        linhas.append('      <attribute id="g0" title="representacao" type="string" />')
        linhas.append('    </attributes>')
        linhas.append('    <attvalues>')
        linhas.append(f'      <attvalue for="g0" value="{self._escapar_xml(representacao)}" />')
        linhas.append('    </attvalues>')

        linhas.append('    <attributes class="edge" mode="static">')
        linhas.append('      <attribute id="0" title="tipo_relacao" type="string" />')
        linhas.append('      <attribute id="1" title="peso_original" type="double" />')
        linhas.append('      <attribute id="2" title="representacao_origem" type="string" />')
        linhas.append('    </attributes>')

        linhas.append('    <nodes>')
        for indice in sorted(vertices.keys()):
            label = vertices[indice]
            linhas.append(
                f'      <node id="{self._escapar_xml(indice)}" label="{self._escapar_xml(label)}" />'
            )
        linhas.append('    </nodes>')

        linhas.append('    <edges>')
        id_aresta = 0
        for origem, destino in sorted(arestas.keys()):
            peso_original = arestas[(origem, destino)]
            peso_visual = pesos_visuais.get((origem, destino), peso_original)

            linhas.append(
                f'      <edge id="{id_aresta}" '
                f'source="{self._escapar_xml(origem)}" '
                f'target="{self._escapar_xml(destino)}" '
                f'weight="{self._escapar_xml(peso_visual)}">'
            )
            linhas.append('        <attvalues>')
            linhas.append(f'          <attvalue for="0" value="{self._escapar_xml(tipo_relacao)}" />')
            linhas.append(f'          <attvalue for="1" value="{self._escapar_xml(peso_original)}" />')
            linhas.append(f'          <attvalue for="2" value="{self._escapar_xml(representacao)}" />')
            linhas.append('        </attvalues>')
            linhas.append('      </edge>')
            id_aresta += 1

        linhas.append('    </edges>')
        linhas.append('  </graph>')
        linhas.append('</gexf>')

        return "\n".join(linhas)

    def _salvar_gexf(self, nome_arquivo: str, conteudo: str) -> Path:
        """Salva o arquivo GEXF na pasta de saída."""
        self.pasta_saida.mkdir(parents=True, exist_ok=True)
        caminho_saida = self.pasta_saida / nome_arquivo
        with caminho_saida.open("w", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)
        return caminho_saida

    def _exportar_objeto_grafo(self, grafo, nome_arquivo_saida: str, nome_grafo: str, tipo_relacao: str, representacao: str) -> Path:
        """Exporta um objeto de grafo já construído para GEXF."""
        arestas = self._extrair_arestas_do_grafo(grafo)
        vertices = self._obter_vertices_para_exportacao(grafo, arestas)
        conteudo = self._gerar_gexf(nome_grafo, representacao, vertices, arestas, tipo_relacao)
        caminho = self._salvar_gexf(nome_arquivo_saida, conteudo)

        print(
            f"Exportado: {caminho} "
            f"| representacao={representacao} "
            f"| vertices={len(vertices)} "
            f"| arestas={len(arestas)}"
        )
        return caminho

    # ------------------------------------------------------
    # Construção usando construir_todos()
    # ------------------------------------------------------

    def _construir_todos_filtrado(self, nomes_arquivos: List[str]):
        """
        Chama o método construir_todos() do construtor.

        Retorno esperado:
            Tuple[AdjacencyListGraph, AdjacencyMatrixGraph]
        """
        construtor = ConstrucaoFiltrada(
            nomes_arquivos=nomes_arquivos,
            dados_processados=self.dados_processados,
            arquivo_mapeamento=self.arquivo_mapeamento,
        )
        return construtor.construir_todos()

    def exportar_representacoes_do_grafo(self, nomes_arquivos: List[str], prefixo_saida: str, nome_grafo: str, tipo_relacao: str) -> List[Path]:
        """
        Constrói um grafo chamando construir_todos() e exporta as duas representações.
        """
        grafo_lista, grafo_matriz = self._construir_todos_filtrado(nomes_arquivos)

        saidas = []
        saidas.append(self._exportar_objeto_grafo(
            grafo=grafo_lista,
            nome_arquivo_saida=f"{prefixo_saida}_lista_adjacencia.gexf",
            nome_grafo=nome_grafo,
            tipo_relacao=tipo_relacao,
            representacao="AdjacencyListGraph",
        ))

        saidas.append(self._exportar_objeto_grafo(
            grafo=grafo_matriz,
            nome_arquivo_saida=f"{prefixo_saida}_matriz_adjacencia.gexf",
            nome_grafo=nome_grafo,
            tipo_relacao=tipo_relacao,
            representacao="AdjacencyMatrixGraph",
        ))

        return saidas

    # ------------------------------------------------------
    # Métodos públicos mantidos para compatibilidade
    # ------------------------------------------------------

    def exportar_grafo_de_arquivo(self, nome_arquivo_json: str, nome_arquivo_saida: str, nome_grafo: str, tipo_relacao: str) -> List[Path]:
        """
        Exporta um grafo individual a partir de um JSON.

        Observação:
        - O parâmetro nome_arquivo_saida é mantido por compatibilidade, mas o
          nome final recebe sufixo de representação:
            *_lista_adjacencia.gexf
            *_matriz_adjacencia.gexf
        """
        prefixo = nome_arquivo_saida.replace(".gexf", "")
        return self.exportar_representacoes_do_grafo(
            nomes_arquivos=[nome_arquivo_json],
            prefixo_saida=prefixo,
            nome_grafo=nome_grafo,
            tipo_relacao=tipo_relacao,
        )

    def exportar_grafo_integrado(self) -> List[Path]:
        """Exporta o grafo integrado nas duas representações."""
        arquivos = ["comentarios.json", "fechamentos.json", "reviews_merges.json"]
        return self.exportar_representacoes_do_grafo(
            nomes_arquivos=arquivos,
            prefixo_saida="grafo_4_integrado",
            nome_grafo="Grafo 4 - Integrado",
            tipo_relacao="integrado",
        )

    def exportar_todos(self) -> List[Path]:
        """
        Exporta os quatro grafos esperados pelo trabalho, em duas representações.

        Arquivos gerados:
            - grafo_1_comentarios_lista_adjacencia.gexf
            - grafo_1_comentarios_matriz_adjacencia.gexf
            - grafo_2_fechamentos_lista_adjacencia.gexf
            - grafo_2_fechamentos_matriz_adjacencia.gexf
            - grafo_3_reviews_merges_lista_adjacencia.gexf
            - grafo_3_reviews_merges_matriz_adjacencia.gexf
            - grafo_4_integrado_lista_adjacencia.gexf
            - grafo_4_integrado_matriz_adjacencia.gexf
        """
        saidas: List[Path] = []

        saidas.extend(self.exportar_grafo_de_arquivo(
            nome_arquivo_json="comentarios.json",
            nome_arquivo_saida="grafo_1_comentarios.gexf",
            nome_grafo="Grafo 1 - Comentários em issues e PRs",
            tipo_relacao="comentario",
        ))

        saidas.extend(self.exportar_grafo_de_arquivo(
            nome_arquivo_json="fechamentos.json",
            nome_arquivo_saida="grafo_2_fechamentos.gexf",
            nome_grafo="Grafo 2 - Fechamentos de issues",
            tipo_relacao="fechamento",
        ))

        saidas.extend(self.exportar_grafo_de_arquivo(
            nome_arquivo_json="reviews_merges.json",
            nome_arquivo_saida="grafo_3_reviews_merges.gexf",
            nome_grafo="Grafo 3 - Reviews, aprovações e merges",
            tipo_relacao="review_merge",
        ))

        saidas.extend(self.exportar_grafo_integrado())
        return saidas


# ==========================================================
# EXECUÇÃO POR LINHA DE COMANDO
# ==========================================================


def executar_por_linha_de_comando():
    parser = argparse.ArgumentParser(description="Exporta os 4 grafos para GEXF usando Construcao.construir_todos().")
    parser.add_argument("--dados", default=None, help="Caminho para dados_processados")
    parser.add_argument("--mapeamento", default=None, help="Caminho para mapeamento_vertices.json")
    parser.add_argument("--saida", default=None, help="Pasta de saída")
    parser.add_argument(
        "--com-isolados",
        action="store_true",
        help="Exporta também vértices sem arestas.",
    )
    parser.add_argument(
        "--manter-auto-lacos",
        action="store_true",
        help="Mantém arestas em que origem e destino são o mesmo vértice.",
    )
    parser.add_argument(
        "--sem-normalizar-pesos",
        action="store_true",
        help="Usa o peso real no atributo weight. Pode prejudicar a visualização no Gephi.",
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
    print("Construção usada: Construcao.construir_todos()")
    print()

    exportador.exportar_todos()


if __name__ == "__main__":
    executar_por_linha_de_comando()
