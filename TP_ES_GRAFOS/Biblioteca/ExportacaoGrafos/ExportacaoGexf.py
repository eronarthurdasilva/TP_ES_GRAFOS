"""ExportacaoGexf.py
===================

Exporta os 4 grafos do trabalho para GEXF, formato aceito pelo Gephi.

Esta implementação NÃO usa biblioteca de grafos, como NetworkX, igraph ou graph-tool.
Ela usa apenas recursos básicos do Python e bibliotecas padrão: dict, list, json,
pathlib, argparse e math.

Ajustes para visualização no Gephi:
- Por padrão, exporta apenas vértices que possuem arestas.
- Por padrão, ignora auto-laços (arestas de um vértice para ele mesmo).
- Por padrão, normaliza o peso visual da aresta para evitar que o Gephi desenhe
  arestas gigantes. O peso original fica preservado no atributo peso_original.

Entrada esperada:
    dados_processados/
        comentarios.json
        fechamentos.json
        reviews_merges.json

Cada JSON deve conter interações com os campos principais:
    de      -> origem da aresta
    para    -> destino da aresta
    peso    -> peso da aresta

Também são aceitos nomes alternativos:
    origem/source/from
    destino/target/to
    peso/weight
"""

import argparse
import json
import math
from pathlib import Path


class ExportacaoGexf:
    """Classe responsável por exportar os grafos para arquivos .gexf."""

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

        # Importante para o Gephi: se True, aparecem milhares de nós soltos.
        # Para visualização, normalmente é melhor deixar False.
        self.exportar_vertices_isolados = exportar_vertices_isolados

        # Auto-laço = aresta de um vértice para ele mesmo. No Gephi, muitos
        # auto-laços podem virar desenhos grandes/estranhos e atrapalhar a leitura.
        self.ignorar_auto_lacos = ignorar_auto_lacos

        # O peso real pode ser muito alto. Se ele for usado diretamente no campo
        # weight, o Gephi pode desenhar arestas enormes. Por isso, usamos um peso
        # visual normalizado no GEXF e guardamos o peso real em peso_original.
        self.normalizar_pesos_gephi = normalizar_pesos_gephi
        self.peso_visual_minimo = float(peso_visual_minimo)
        self.peso_visual_maximo = float(peso_visual_maximo)

        self._mapeamento_cache = None

    # Caminhos e leitura de arquivos

    def _descobrir_arquivo_mapeamento(self):
        """Procura o arquivo de mapeamento em locais comuns."""
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

    def _escapar_xml(self, valor):
        """Escapa caracteres especiais para não quebrar o XML/GEXF."""
        texto = str(valor)
        texto = texto.replace("&", "&amp;")
        texto = texto.replace("<", "&lt;")
        texto = texto.replace(">", "&gt;")
        texto = texto.replace('"', "&quot;")
        texto = texto.replace("'", "&apos;")
        return texto

    def _carregar_mapeamento(self):
        """
        Carrega o mapeamento login -> índice.

        Relação com teoria dos grafos:
        - Cada login representa um vértice.
        - O índice é o identificador usado internamente no GEXF.
        """
        if self._mapeamento_cache is not None:
            return self._mapeamento_cache

        if not self.arquivo_mapeamento.exists():
            raise FileNotFoundError(
                "Arquivo de mapeamento não encontrado.\n"
                f"Caminho procurado: {self.arquivo_mapeamento}\n"
                "Soluções:\n"
                "1) Rode primeiro: python ConstrucaoGrafos/MapeamentoVertices.py\n"
                "2) Ou copie mapeamento_vertices.json para dentro de ExportacaoGrafos\n"
                "3) Ou informe o caminho manualmente em RodarExportacao.py"
            )

        with self.arquivo_mapeamento.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        if isinstance(dados, dict) and "global" in dados:
            mapeamento = dados["global"].get("mapeamento", {})
        else:
            mapeamento = dados

        if not isinstance(mapeamento, dict):
            raise ValueError("Formato inválido para o arquivo de mapeamento de vértices.")

        self._mapeamento_cache = {}
        for login, indice in mapeamento.items():
            login_normalizado = str(login).strip()
            if login_normalizado == "":
                continue
            self._mapeamento_cache[login_normalizado] = int(indice)

        return self._mapeamento_cache

    def _carregar_itens_json(self, arquivo_json):
        """Lê um JSON processado e devolve uma lista de dicionários."""
        if not arquivo_json.exists():
            print(f"Aviso: arquivo não encontrado: {arquivo_json}")
            return []

        with arquivo_json.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        if isinstance(dados, list):
            return [item for item in dados if isinstance(item, dict)]

        if isinstance(dados, dict):
            for chave in ("nodes", "items", "edges", "arestas", "interacoes"):
                itens = dados.get(chave)
                if isinstance(itens, list):
                    return [item for item in itens if isinstance(item, dict)]
            return [dados]

        return []

    # Normalização de interações para arestas

    def _pegar_primeiro_campo(self, item, nomes):
        """Busca o primeiro campo existente dentro do dicionário."""
        for nome in nomes:
            if nome in item:
                return item[nome]
        return None

    def _converter_peso(self, valor):
        """Converte o peso da aresta para float."""
        if valor is None:
            return 1.0
        try:
            peso = float(valor)
            if peso < 0:
                return 0.0
            return peso
        except Exception:
            return 1.0

    def _agrupar_arestas(self, arquivos):
        """
        Lê um ou mais arquivos JSON e agrupa arestas repetidas.

        Retorna:
            {
                (origem, destino): peso_total
            }

        Relação com teoria dos grafos:
        - origem e destino formam uma aresta direcionada.
        - peso_total representa a intensidade acumulada da relação.
        """
        mapeamento = self._carregar_mapeamento()
        arestas = {}

        total_itens_lidos = 0
        total_sem_origem_destino = 0
        total_fora_do_mapeamento = 0
        total_auto_lacos_ignorados = 0

        for nome_arquivo in arquivos:
            caminho = self.dados_processados / nome_arquivo
            itens = self._carregar_itens_json(caminho)
            total_itens_lidos += len(itens)

            for item in itens:
                origem_nome = self._pegar_primeiro_campo(item, ["de", "origem", "source", "from"])
                destino_nome = self._pegar_primeiro_campo(item, ["para", "destino", "target", "to"])
                peso = self._pegar_primeiro_campo(item, ["peso", "weight"])

                if origem_nome is None or destino_nome is None:
                    total_sem_origem_destino += 1
                    continue

                origem_nome = str(origem_nome).strip()
                destino_nome = str(destino_nome).strip()

                if origem_nome == "" or destino_nome == "":
                    total_sem_origem_destino += 1
                    continue

                if origem_nome not in mapeamento or destino_nome not in mapeamento:
                    total_fora_do_mapeamento += 1
                    continue

                origem = mapeamento[origem_nome]
                destino = mapeamento[destino_nome]

                if self.ignorar_auto_lacos and origem == destino:
                    total_auto_lacos_ignorados += 1
                    continue

                chave = (origem, destino)

                if chave not in arestas:
                    arestas[chave] = 0.0

                arestas[chave] += self._converter_peso(peso)

        if len(arestas) == 0:
            print("Aviso: nenhuma aresta foi gerada para:", ", ".join(arquivos))
            print(f"  Itens lidos: {total_itens_lidos}")
            print(f"  Itens sem origem/destino: {total_sem_origem_destino}")
            print(f"  Itens fora do mapeamento: {total_fora_do_mapeamento}")
            print(f"  Auto-laços ignorados: {total_auto_lacos_ignorados}")
            print("  Verifique se os usuários dos JSONs também existem no mapeamento_vertices.json.")
        else:
            print(
                "Resumo da leitura:", ", ".join(arquivos),
                f"| itens={total_itens_lidos}",
                f"| arestas={len(arestas)}",
                f"| sem_origem_destino={total_sem_origem_destino}",
                f"| fora_mapeamento={total_fora_do_mapeamento}",
                f"| auto_lacos_ignorados={total_auto_lacos_ignorados}",
            )

        return arestas

    def _obter_vertices_para_exportacao(self, arestas):
        """Define quais vértices serão escritos no GEXF."""
        mapeamento = self._carregar_mapeamento()
        indice_para_login = {}

        for login, indice in mapeamento.items():
            indice_para_login[indice] = login

        if self.exportar_vertices_isolados:
            return indice_para_login

        vertices_usados = set()
        for origem, destino in arestas.keys():
            vertices_usados.add(origem)
            vertices_usados.add(destino)

        vertices = {}
        for indice in vertices_usados:
            if indice in indice_para_login:
                vertices[indice] = indice_para_login[indice]

        return vertices

    # Tratamento dos pesos para visualização no Gephi

    def _normalizar_pesos_para_gephi(self, arestas):
        """
        Converte pesos reais em pesos visuais menores.

        Por que isso existe?
        - O peso real pode ser muito alto, por exemplo 500, 1000 ou mais.
        - Se esse número for usado diretamente no atributo weight, o Gephi pode
          desenhar arestas grossas demais, parecendo grandes polígonos cinza.
        - Por isso, o GEXF recebe um peso visual entre peso_visual_minimo e
          peso_visual_maximo.
        - O peso real continua salvo no atributo peso_original.

        Relação com grafos:
        - O grafo continua ponderado.
        - Apenas separamos o peso real da aresta do peso usado para visualização.
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
    
    # Escrita do GEXF

    def _gerar_gexf(self, nome_grafo, vertices, arestas, tipo_relacao):
        """Gera o conteúdo textual do arquivo .gexf."""
        pesos_visuais = self._normalizar_pesos_para_gephi(arestas)

        linhas = []

        linhas.append('<?xml version="1.0" encoding="UTF-8"?>')
        linhas.append('<gexf xmlns="http://www.gexf.net/1.2draft" version="1.2">')
        linhas.append('  <meta>')
        linhas.append('    <creator>ExportacaoGrafos - Python puro</creator>')
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

    # Métodos públicos

    def exportar_grafo_de_arquivo(self, nome_arquivo_json, nome_arquivo_saida, nome_grafo, tipo_relacao):
        """Exporta um grafo individual a partir de um JSON."""
        arestas = self._agrupar_arestas([nome_arquivo_json])
        vertices = self._obter_vertices_para_exportacao(arestas)

        conteudo = self._gerar_gexf(nome_grafo, vertices, arestas, tipo_relacao)
        caminho = self._salvar_gexf(nome_arquivo_saida, conteudo)

        print(f"Exportado: {caminho} | vertices={len(vertices)} | arestas={len(arestas)}")
        return caminho

    def exportar_grafo_integrado(self):
        """Exporta o grafo integrado, somando os três arquivos de interações."""
        arquivos = ["comentarios.json", "fechamentos.json", "reviews_merges.json"]
        arestas = self._agrupar_arestas(arquivos)
        vertices = self._obter_vertices_para_exportacao(arestas)

        conteudo = self._gerar_gexf("Grafo 4 - Integrado", vertices, arestas, "integrado")
        caminho = self._salvar_gexf("grafo_4_integrado.gexf", conteudo)

        print(f"Exportado: {caminho} | vertices={len(vertices)} | arestas={len(arestas)}")
        return caminho

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

    exportador.exportar_todos()


if __name__ == "__main__":
    executar_por_linha_de_comando()
