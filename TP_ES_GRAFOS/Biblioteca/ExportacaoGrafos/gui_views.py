"""
gui_views.py

Camada de visualização textual para os resultados dos grafos e métricas.

Este arquivo representa a parte de "saída" da interface programática simples.
Ele usa o backend definido em gui_backend.py e mostra:
- resumo dos grafos;
- Top-5 por centralidade;
- comunidades detectadas;
- tabelas formatadas;
- indicação dos arquivos CSV/JSON exportados.

Não utiliza bibliotecas de interface gráfica. A saída é feita no terminal,
facilitando a integração com o projeto atual.
"""

from gui_backend import executar_backend, arredondar


# ==========================================================
# FORMATAÇÃO BÁSICA
# ==========================================================

def formatar_valor(valor):
    """
    Formata valores para exibição em tabelas.

    Parâmetros:
        valor (any): valor a ser formatado.

    Retorno:
        str: valor convertido para texto.
    """
    if isinstance(valor, float):
        return str(round(valor, 6))

    if valor is None:
        return ""

    return str(valor)


def formatar_tabela(cabecalhos, linhas):
    """
    Monta uma tabela textual alinhada para exibição no terminal.

    Parâmetros:
        cabecalhos (list[str]): nomes das colunas.
        linhas (list[list]): valores das linhas.

    Retorno:
        str: tabela formatada.
    """
    dados = []
    dados.append([str(cabecalho) for cabecalho in cabecalhos])

    for linha in linhas:
        dados.append([formatar_valor(valor) for valor in linha])

    larguras = []

    for indice_coluna in range(len(cabecalhos)):
        maior = 0
        for linha in dados:
            tamanho = len(linha[indice_coluna])
            if tamanho > maior:
                maior = tamanho
        larguras.append(maior)

    linhas_formatadas = []

    for indice_linha, linha in enumerate(dados):
        partes = []
        for indice_coluna, valor in enumerate(linha):
            partes.append(valor.ljust(larguras[indice_coluna]))

        linhas_formatadas.append(" | ".join(partes))

        if indice_linha == 0:
            separadores = []
            for largura in larguras:
                separadores.append("-" * largura)
            linhas_formatadas.append("-+-".join(separadores))

    return "\n".join(linhas_formatadas)


def imprimir_titulo(texto):
    """
    Imprime um título destacado no terminal.

    Parâmetros:
        texto (str): título a ser exibido.
    """
    print()
    print("=" * 80)
    print(texto)
    print("=" * 80)


def imprimir_subtitulo(texto):
    """
    Imprime um subtítulo destacado no terminal.

    Parâmetros:
        texto (str): subtítulo a ser exibido.
    """
    print()
    print("-" * 80)
    print(texto)
    print("-" * 80)


# ==========================================================
# VIEWS DOS RESULTADOS
# ==========================================================

def mostrar_resumo_grafo(resultado_grafo):
    """
    Mostra o resumo estrutural de um grafo.

    Parâmetros:
        resultado_grafo (dict): resultado consolidado de um grafo,
        produzido pelo backend.
    """
    resumo = resultado_grafo["resumo"]

    cabecalhos = ["Métrica", "Valor"]
    linhas = [
        ["Vértices", resumo["quantidade_vertices"]],
        ["Arestas direcionadas", resumo["quantidade_arestas_direcionadas"]],
        ["Arestas não direcionadas", resumo["quantidade_arestas_nao_direcionadas"]],
        ["Peso total das interações", arredondar(resumo["peso_total_interacoes"])],
        ["Densidade direcionada", arredondar(resumo["densidade_direcionada"])],
        ["Densidade não direcionada", arredondar(resumo["densidade_nao_direcionada"])]
    ]

    print(formatar_tabela(cabecalhos, linhas))


def mostrar_top5_centralidade(resultado_grafo):
    """
    Mostra os 5 usuários mais centrais do grafo.

    A centralidade utilizada é a centralidade de grau, calculada a partir da
    quantidade de vizinhos distintos do usuário.

    Parâmetros:
        resultado_grafo (dict): resultado consolidado de um grafo.
    """
    cabecalhos = [
        "#",
        "Usuário",
        "Grau",
        "Centralidade",
        "Entrada",
        "Saída",
        "Grau ponderado"
    ]

    linhas = []

    for posicao, item in enumerate(resultado_grafo["top_5_centralidade"], start=1):
        linhas.append([
            posicao,
            item["usuario"],
            item["grau_total"],
            arredondar(item["centralidade_grau"]),
            item["grau_entrada"],
            item["grau_saida"],
            arredondar(item["grau_ponderado"])
        ])

    print(formatar_tabela(cabecalhos, linhas))


def mostrar_comunidades(resultado_grafo):
    """
    Mostra as principais comunidades detectadas no grafo.

    Parâmetros:
        resultado_grafo (dict): resultado consolidado de um grafo.
    """
    cabecalhos = ["Comunidade", "Tamanho", "Amostra de membros"]
    linhas = []

    for comunidade in resultado_grafo["comunidades_detectadas"]:
        membros = ", ".join(comunidade["amostra_membros"])
        linhas.append([
            comunidade["id_comunidade"],
            comunidade["tamanho"],
            membros
        ])

    print(formatar_tabela(cabecalhos, linhas))


def mostrar_metricas_estrutura_coesao(resultado_grafo):
    """
    Mostra métricas de estrutura e coesão caso tenham sido carregadas da pasta
    Metricas/saida_metricas/estrutura_coesao.

    Parâmetros:
        resultado_grafo (dict): resultado consolidado de um grafo.
    """
    metricas = resultado_grafo.get("metricas_estrutura_coesao")

    if not metricas:
        print("Métricas externas de estrutura/coesão não encontradas para este grafo.")
        return

    cabecalhos = ["Métrica", "Valor"]
    linhas = [
        ["Coeficiente de aglomeração médio", arredondar(metricas.get("coeficiente_aglomeracao_medio_todos_vertices"))],
        ["Coeficiente de aglomeração, grau >= 2", arredondar(metricas.get("coeficiente_aglomeracao_medio_grau_maior_igual_2"))],
        ["Assortatividade por grau", arredondar(metricas.get("assortatividade_por_grau"))],
        ["Interpretação densidade", metricas.get("interpretacao_densidade")],
        ["Interpretação aglomeração", metricas.get("interpretacao_aglomeracao")],
        ["Interpretação assortatividade", metricas.get("interpretacao_assortatividade")]
    ]

    print(formatar_tabela(cabecalhos, linhas))


def mostrar_resultado_grafo(resultado_grafo):
    """
    Mostra todos os blocos de saída de um grafo.

    Parâmetros:
        resultado_grafo (dict): resultado consolidado de um grafo.
    """
    imprimir_titulo(resultado_grafo["nome_grafo"])

    imprimir_subtitulo("Resumo do grafo")
    mostrar_resumo_grafo(resultado_grafo)

    imprimir_subtitulo("Top-5 por centralidade")
    mostrar_top5_centralidade(resultado_grafo)

    imprimir_subtitulo("Comunidades detectadas")
    mostrar_comunidades(resultado_grafo)

    imprimir_subtitulo("Métricas de estrutura e coesão carregadas")
    mostrar_metricas_estrutura_coesao(resultado_grafo)


def mostrar_resultados(resultado_final):
    """
    Mostra os resultados de todos os grafos.

    Parâmetros:
        resultado_final (dict): resultado completo produzido por executar_backend().
    """
    imprimir_titulo("RESULTADOS DOS GRAFOS")

    print(f"Pasta de dados processados: {resultado_final['pasta_dados_processados']}")
    print(f"Pasta de saída: {resultado_final['pasta_saida']}")
    print(f"Quantidade de grafos analisados: {resultado_final['quantidade_grafos']}")

    for resultado_grafo in resultado_final["grafos"]:
        mostrar_resultado_grafo(resultado_grafo)

    imprimir_titulo("ARQUIVOS EXPORTADOS")
    print(f"{resultado_final['pasta_saida']}/resultado_gui.json")
    print(f"{resultado_final['pasta_saida']}/resumo_grafos.csv")
    print(f"{resultado_final['pasta_saida']}/top5_centralidade.csv")
    print(f"{resultado_final['pasta_saida']}/comunidades_detectadas.csv")


def executar_view():
    """
    Executa o fluxo completo da view.

    Fluxo:
        1. Chama o backend.
        2. Recebe os resultados.
        3. Mostra tabelas formatadas no terminal.
        4. Informa onde os CSVs/JSON foram exportados.
    """
    resultado_final = executar_backend()
    mostrar_resultados(resultado_final)


if __name__ == "__main__":
    executar_view()
