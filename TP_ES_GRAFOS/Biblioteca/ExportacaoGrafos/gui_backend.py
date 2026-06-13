"""
gui_backend.py

Backend programático para conectar os grafos do projeto com as métricas
necessárias para visualização/saída em uma interface simples.

Este arquivo NÃO utiliza bibliotecas de grafos, como NetworkX, igraph ou graph-tool.
A representação dos grafos é feita apenas com estruturas nativas do Python:
- dict
- list
- set
- tuple

Responsabilidades principais:
1. Carregar os dados processados dos grafos.
2. Construir uma representação interna simples dos grafos.
3. Calcular resumo do grafo.
4. Calcular Top-5 por centralidade de grau.
5. Detectar comunidades de forma simples, via propagação de rótulos.
6. Exportar os resultados em JSON e CSV.
"""

import json
import csv
from pathlib import Path

# CONFIGURAÇÃO DOS GRAFOS ESPERADOS

GRAFOS_CONFIG = {
    "comentarios": {
        "nome": "Grafo 1 - Comentários em issues e PRs",
        "arquivo": "comentarios.json"
    },
    "fechamentos": {
        "nome": "Grafo 2 - Fechamentos de issues",
        "arquivo": "fechamentos.json"
    },
    "reviews_merges": {
        "nome": "Grafo 3 - Reviews, aprovações e merges",
        "arquivo": "reviews_merges.json"
    }
}



# LOCALIZAÇÃO DE PASTAS


def localizar_pasta_raiz():
    """
    Localiza a pasta raiz do projeto.

    A estrutura esperada é:

    Projeto/
    ├── ExportacaoGrafos/
    │   ├── gui_backend.py
    │   └── gui_views.py
    ├── ExtracaoDados/
    │   └── dados_processados/
    └── Metricas/

    Como este arquivo fica dentro de ExportacaoGrafos, a raiz é a pasta pai.

    Retorno:
        Path: caminho da pasta raiz do projeto.
    """
    return Path(__file__).resolve().parent.parent


def localizar_pasta_dados_processados(pasta_raiz=None):
    """
    Localiza automaticamente a pasta que contém os JSONs processados.

    Parâmetros:
        pasta_raiz (Path | str | None): pasta raiz do projeto. Se None,
        a função tenta localizar automaticamente.

    Retorno:
        Path: caminho da pasta de dados processados.

    Exceção:
        FileNotFoundError: caso a pasta não seja encontrada.
    """
    if pasta_raiz is None:
        pasta_raiz = localizar_pasta_raiz()
    else:
        pasta_raiz = Path(pasta_raiz)

    pasta_atual = Path(__file__).resolve().parent

    opcoes = [
        pasta_raiz / "ExtracaoDados" / "dados_processados",
        pasta_raiz / "ExtracaoDados" / "DadosProcessados",
        pasta_raiz / "dados_processados",
        pasta_atual / "dados_processados",
        pasta_atual / "dados_exemplo_processados"
    ]

    for opcao in opcoes:
        if opcao.exists():
            return opcao

    raise FileNotFoundError(
        "Não encontrei a pasta de dados processados. "
        "Verifique se existe ExtracaoDados/dados_processados."
    )


def localizar_pasta_saida():
    """
    Define a pasta de saída para os resultados gerados pelo backend/views.

    Retorno:
        Path: ExportacaoGrafos/saida_gui
    """
    return Path(__file__).resolve().parent / "saida_gui"



# LEITURA E NORMALIZAÇÃO DOS DADOS


def carregar_json(caminho_arquivo):
    """
    Carrega um arquivo JSON.

    Parâmetros:
        caminho_arquivo (str | Path): caminho do arquivo JSON.

    Retorno:
        list | dict: conteúdo carregado do JSON.
    """
    caminho_arquivo = Path(caminho_arquivo)

    if not caminho_arquivo.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")

    with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def extrair_lista_registros(conteudo_json):
    """
    Extrai a lista de interações de um conteúdo JSON.

    Formato principal esperado:
        [
            {"de": "usuario_a", "para": "usuario_b", "peso": 3}
        ]

    Também aceita formatos com a lista dentro de chaves como:
    "arestas", "edges", "dados", "interacoes", "registros" ou "items".

    Parâmetros:
        conteudo_json (list | dict): conteúdo lido do arquivo JSON.

    Retorno:
        list: lista de registros/interações.
    """
    if isinstance(conteudo_json, list):
        return conteudo_json

    if isinstance(conteudo_json, dict):
        chaves_possiveis = [
            "arestas",
            "edges",
            "dados",
            "interacoes",
            "registros",
            "items"
        ]

        for chave in chaves_possiveis:
            if chave in conteudo_json and isinstance(conteudo_json[chave], list):
                return conteudo_json[chave]

    raise ValueError("Formato de JSON não reconhecido. Esperava uma lista de interações.")


def obter_valor(registro, nomes_possiveis):
    """
    Busca um valor no registro considerando nomes alternativos.

    Exemplo:
        origem pode aparecer como "de", "origem", "source" ou "from".
        destino pode aparecer como "para", "destino", "target" ou "to".

    Parâmetros:
        registro (dict): registro bruto da interação.
        nomes_possiveis (list): nomes de campos que podem conter o valor.

    Retorno:
        any | None: valor encontrado ou None.
    """
    for nome in nomes_possiveis:
        if nome in registro:
            return registro[nome]
    return None


def converter_peso(valor):
    """
    Converte o peso da interação para float.

    Em grafos ponderados, o peso representa a intensidade da aresta.
    Neste projeto, pode representar número de comentários, fechamentos,
    reviews, aprovações, merges ou a soma dessas interações.

    Parâmetros:
        valor (any): valor bruto do peso.

    Retorno:
        float: peso convertido. Caso o valor esteja vazio ou inválido,
        retorna 1.0.
    """
    if valor is None or valor == "":
        return 1.0

    try:
        return float(valor)
    except Exception:
        return 1.0


def normalizar_registro(registro):
    """
    Normaliza um registro bruto em uma aresta padronizada.

    Retorno:
        tuple: (origem, destino, peso)

    Relação com grafos:
        - origem e destino são vértices.
        - origem -> destino é uma aresta direcionada.
        - peso representa a intensidade da interação.
    """
    if not isinstance(registro, dict):
        raise ValueError(f"Registro inválido. Esperava dicionário: {registro}")

    origem = obter_valor(registro, ["de", "origem", "source", "from", "autor", "user_from"])
    destino = obter_valor(registro, ["para", "destino", "target", "to", "receptor", "user_to"])
    peso = obter_valor(registro, ["peso", "weight", "valor", "quantidade", "count"])

    if origem is None or destino is None:
        raise ValueError(f"Registro sem origem ou destino: {registro}")

    origem = str(origem).strip()
    destino = str(destino).strip()

    if origem == "" or destino == "":
        raise ValueError(f"Registro com origem ou destino vazio: {registro}")

    return origem, destino, converter_peso(peso)



# CONSTRUÇÃO INTERNA DO GRAFO


def construir_grafo(nome_grafo, registros, ignorar_auto_lacos=True):
    """
    Constrói uma representação interna simples do grafo.

    Parâmetros:
        nome_grafo (str): nome descritivo do grafo.
        registros (list): lista de interações do grafo.
        ignorar_auto_lacos (bool): se True, ignora arestas do tipo A -> A.

    Retorno:
        dict: estrutura contendo:
            - nome_grafo
            - vertices
            - arestas_direcionadas
            - arestas_nao_direcionadas
            - adjacencia_direcionada_saida
            - adjacencia_direcionada_entrada
            - adjacencia_nao_direcionada

    Relação com grafos:
        A estrutura representa G = (V, E), em que:
            V = conjunto de usuários
            E = conjunto de interações entre usuários
    """
    vertices = set()
    arestas_direcionadas = {}
    adj_saida = {}
    adj_entrada = {}

    for registro in registros:
        origem, destino, peso = normalizar_registro(registro)

        if ignorar_auto_lacos and origem == destino:
            continue

        vertices.add(origem)
        vertices.add(destino)

        chave = (origem, destino)
        if chave not in arestas_direcionadas:
            arestas_direcionadas[chave] = 0.0
        arestas_direcionadas[chave] += peso

        adj_saida.setdefault(origem, set()).add(destino)
        adj_entrada.setdefault(destino, set()).add(origem)
        adj_saida.setdefault(destino, set())
        adj_entrada.setdefault(origem, set())

    arestas_nao_direcionadas = converter_para_nao_direcionado(arestas_direcionadas)
    adj_nao_direcionada = montar_lista_adjacencia_nao_direcionada(vertices, arestas_nao_direcionadas)

    return {
        "nome_grafo": nome_grafo,
        "vertices": vertices,
        "arestas_direcionadas": arestas_direcionadas,
        "arestas_nao_direcionadas": arestas_nao_direcionadas,
        "adjacencia_direcionada_saida": adj_saida,
        "adjacencia_direcionada_entrada": adj_entrada,
        "adjacencia_nao_direcionada": adj_nao_direcionada
    }


def converter_para_nao_direcionado(arestas_direcionadas):
    """
    Converte as arestas direcionadas em arestas não direcionadas.

    Exemplo:
        A -> B e B -> A são agrupadas em A -- B.

    Parâmetros:
        arestas_direcionadas (dict): {(origem, destino): peso}

    Retorno:
        dict: {(vertice_a, vertice_b): peso_total}
    """
    arestas_nao_direcionadas = {}

    for origem, destino in arestas_direcionadas:
        if origem == destino:
            continue

        peso = arestas_direcionadas[(origem, destino)]

        if origem < destino:
            chave = (origem, destino)
        else:
            chave = (destino, origem)

        if chave not in arestas_nao_direcionadas:
            arestas_nao_direcionadas[chave] = 0.0

        arestas_nao_direcionadas[chave] += peso

    return arestas_nao_direcionadas


def montar_lista_adjacencia_nao_direcionada(vertices, arestas_nao_direcionadas):
    """
    Monta uma lista de adjacência não direcionada.

    Parâmetros:
        vertices (set): conjunto de vértices.
        arestas_nao_direcionadas (dict): arestas sem direção.

    Retorno:
        dict: {vertice: {vizinho_1, vizinho_2, ...}}
    """
    adjacencia = {}

    for vertice in vertices:
        adjacencia[vertice] = set()

    for origem, destino in arestas_nao_direcionadas:
        adjacencia.setdefault(origem, set()).add(destino)
        adjacencia.setdefault(destino, set()).add(origem)

    return adjacencia



# RESUMO DO GRAFO


def calcular_resumo_grafo(grafo):
    """
    Calcula um resumo estrutural do grafo.

    Métricas retornadas:
        - quantidade de vértices
        - quantidade de arestas direcionadas
        - quantidade de arestas não direcionadas
        - peso total das interações
        - densidade direcionada
        - densidade não direcionada

    Parâmetros:
        grafo (dict): grafo construído por construir_grafo().

    Retorno:
        dict: resumo do grafo.
    """
    vertices = grafo["vertices"]
    arestas_direcionadas = grafo["arestas_direcionadas"]
    arestas_nao_direcionadas = grafo["arestas_nao_direcionadas"]

    n = len(vertices)
    m_direcionado = len(arestas_direcionadas)
    m_nao_direcionado = len(arestas_nao_direcionadas)
    peso_total = sum(arestas_direcionadas.values())

    if n <= 1:
        densidade_direcionada = 0.0
        densidade_nao_direcionada = 0.0
    else:
        densidade_direcionada = m_direcionado / (n * (n - 1))
        densidade_nao_direcionada = m_nao_direcionado / (n * (n - 1) / 2)

    return {
        "nome_grafo": grafo["nome_grafo"],
        "quantidade_vertices": n,
        "quantidade_arestas_direcionadas": m_direcionado,
        "quantidade_arestas_nao_direcionadas": m_nao_direcionado,
        "peso_total_interacoes": peso_total,
        "densidade_direcionada": densidade_direcionada,
        "densidade_nao_direcionada": densidade_nao_direcionada
    }



# TOP-5 POR CENTRALIDADE


def calcular_centralidades_grau(grafo):
    """
    Calcula centralidades simples baseadas em grau.

    Métricas calculadas por vértice:
        - grau_total: quantidade de vizinhos distintos no grafo não direcionado.
        - centralidade_grau: grau_total / (n - 1).
        - grau_entrada: quantidade de vértices que apontam para o usuário.
        - grau_saida: quantidade de vértices para os quais o usuário aponta.
        - grau_ponderado: soma dos pesos das arestas incidentes.

    Parâmetros:
        grafo (dict): grafo construído por construir_grafo().

    Retorno:
        list[dict]: lista de centralidades por usuário.
    """
    vertices = grafo["vertices"]
    adj_nao_direcionada = grafo["adjacencia_nao_direcionada"]
    adj_saida = grafo["adjacencia_direcionada_saida"]
    adj_entrada = grafo["adjacencia_direcionada_entrada"]
    arestas_nao_direcionadas = grafo["arestas_nao_direcionadas"]

    n = len(vertices)
    pesos_por_vertice = {}

    for vertice in vertices:
        pesos_por_vertice[vertice] = 0.0

    for origem, destino in arestas_nao_direcionadas:
        peso = arestas_nao_direcionadas[(origem, destino)]
        pesos_por_vertice[origem] = pesos_por_vertice.get(origem, 0.0) + peso
        pesos_por_vertice[destino] = pesos_por_vertice.get(destino, 0.0) + peso

    resultados = []

    for vertice in vertices:
        grau_total = len(adj_nao_direcionada.get(vertice, set()))
        grau_saida = len(adj_saida.get(vertice, set()))
        grau_entrada = len(adj_entrada.get(vertice, set()))

        if n <= 1:
            centralidade_grau = 0.0
        else:
            centralidade_grau = grau_total / (n - 1)

        resultados.append({
            "usuario": vertice,
            "grau_total": grau_total,
            "centralidade_grau": centralidade_grau,
            "grau_entrada": grau_entrada,
            "grau_saida": grau_saida,
            "grau_ponderado": pesos_por_vertice.get(vertice, 0.0)
        })

    resultados.sort(
        key=lambda item: (
            item["centralidade_grau"],
            item["grau_ponderado"],
            item["grau_total"],
            item["usuario"]
        ),
        reverse=True
    )

    return resultados


def obter_top_5_centralidade(grafo):
    """
    Retorna os 5 usuários mais centrais do grafo por centralidade de grau.

    Parâmetros:
        grafo (dict): grafo construído por construir_grafo().

    Retorno:
        list[dict]: cinco primeiros usuários mais centrais.
    """
    return calcular_centralidades_grau(grafo)[:5]



# COMUNIDADES DETECTADAS


def detectar_comunidades_label_propagation(grafo, max_iteracoes=20):
    """
    Detecta comunidades usando uma versão simples e determinística de
    propagação de rótulos.

    Ideia do algoritmo:
        1. Cada vértice começa com o próprio rótulo.
        2. Em cada iteração, o vértice observa os rótulos dos vizinhos.
        3. O vértice assume o rótulo mais frequente/pesado entre os vizinhos.
        4. O processo se repete até estabilizar ou atingir o limite de iterações.

    Observação:
        Esta implementação é simples e foi feita sem bibliotecas de grafos.
        Ela é adequada para apresentar comunidades aproximadas na interface.

    Parâmetros:
        grafo (dict): grafo construído por construir_grafo().
        max_iteracoes (int): número máximo de iterações.

    Retorno:
        list[dict]: comunidades detectadas, ordenadas por tamanho.
    """
    vertices = sorted(grafo["vertices"])
    adjacencia = grafo["adjacencia_nao_direcionada"]
    arestas_nao_direcionadas = grafo["arestas_nao_direcionadas"]

    rotulos = {}
    for vertice in vertices:
        rotulos[vertice] = vertice

    for _ in range(max_iteracoes):
        alterou = False

        for vertice in vertices:
            vizinhos = sorted(adjacencia.get(vertice, set()))

            if len(vizinhos) == 0:
                continue

            pontuacao_rotulos = {}

            for vizinho in vizinhos:
                rotulo_vizinho = rotulos[vizinho]

                if vertice < vizinho:
                    chave = (vertice, vizinho)
                else:
                    chave = (vizinho, vertice)

                peso = arestas_nao_direcionadas.get(chave, 1.0)
                pontuacao_rotulos[rotulo_vizinho] = pontuacao_rotulos.get(rotulo_vizinho, 0.0) + peso

            melhor_rotulo = None
            melhor_pontuacao = None

            for rotulo, pontuacao in pontuacao_rotulos.items():
                if melhor_rotulo is None:
                    melhor_rotulo = rotulo
                    melhor_pontuacao = pontuacao
                elif pontuacao > melhor_pontuacao:
                    melhor_rotulo = rotulo
                    melhor_pontuacao = pontuacao
                elif pontuacao == melhor_pontuacao and str(rotulo) < str(melhor_rotulo):
                    melhor_rotulo = rotulo
                    melhor_pontuacao = pontuacao

            if melhor_rotulo is not None and rotulos[vertice] != melhor_rotulo:
                rotulos[vertice] = melhor_rotulo
                alterou = True

        if not alterou:
            break

    grupos = {}
    for vertice, rotulo in rotulos.items():
        grupos.setdefault(rotulo, []).append(vertice)

    comunidades = []
    indice = 1

    for rotulo, membros in grupos.items():
        membros_ordenados = sorted(membros)
        comunidades.append({
            "id_comunidade": indice,
            "rotulo": rotulo,
            "tamanho": len(membros_ordenados),
            "membros": membros_ordenados,
            "amostra_membros": membros_ordenados[:10]
        })
        indice += 1

    comunidades.sort(key=lambda item: item["tamanho"], reverse=True)

    for indice, comunidade in enumerate(comunidades, start=1):
        comunidade["id_comunidade"] = indice

    return comunidades


def obter_resumo_comunidades(grafo, limite=5):
    """
    Retorna um resumo das principais comunidades detectadas.

    Parâmetros:
        grafo (dict): grafo construído por construir_grafo().
        limite (int): quantidade máxima de comunidades retornadas.

    Retorno:
        list[dict]: maiores comunidades, com tamanho e amostra de membros.
    """
    comunidades = detectar_comunidades_label_propagation(grafo)
    return comunidades[:limite]



# MÉTRICAS JÁ GERADAS POR OUTROS ARQUIVOS


def carregar_metricas_estrutura_coesao_se_existir(pasta_raiz=None):
    """
    Tenta carregar o JSON de métricas de estrutura e coesão, caso ele já tenha
    sido gerado pelo arquivo MetricasDeEstruturaCoesao.py.

    Isso permite conectar o backend da interface com as métricas já calculadas
    em outra etapa do projeto.

    Parâmetros:
        pasta_raiz (Path | str | None): pasta raiz do projeto.

    Retorno:
        dict: mapeamento {nome_grafo: metricas}. Retorna dict vazio se o
        arquivo não existir.
    """
    if pasta_raiz is None:
        pasta_raiz = localizar_pasta_raiz()
    else:
        pasta_raiz = Path(pasta_raiz)

    caminho = (
        pasta_raiz
        / "Metricas"
        / "saida_metricas"
        / "estrutura_coesao"
        / "metricas_estrutura_coesao.json"
    )

    if not caminho.exists():
        return {}

    try:
        dados = carregar_json(caminho)
    except Exception:
        return {}

    metricas_por_nome = {}
    if isinstance(dados, list):
        for item in dados:
            if isinstance(item, dict) and "nome_grafo" in item:
                metricas_por_nome[item["nome_grafo"]] = item

    return metricas_por_nome



# ORQUESTRAÇÃO DO BACKEND


def carregar_grafos_processados(pasta_dados_processados):
    """
    Carrega os três grafos principais e monta o grafo integrado.

    Parâmetros:
        pasta_dados_processados (str | Path): pasta com comentarios.json,
        fechamentos.json e reviews_merges.json.

    Retorno:
        dict: {chave_grafo: grafo_construido}
    """
    pasta_dados_processados = Path(pasta_dados_processados)

    registros_por_grafo = {}

    for chave, config in GRAFOS_CONFIG.items():
        caminho_arquivo = pasta_dados_processados / config["arquivo"]
        conteudo = carregar_json(caminho_arquivo)
        registros = extrair_lista_registros(conteudo)
        registros_por_grafo[chave] = registros

    registros_integrados = []
    for chave in registros_por_grafo:
        registros_integrados.extend(registros_por_grafo[chave])

    grafos = {}

    for chave, config in GRAFOS_CONFIG.items():
        grafos[chave] = construir_grafo(config["nome"], registros_por_grafo[chave])

    grafos["integrado"] = construir_grafo("Grafo 4 - Integrado", registros_integrados)

    return grafos


def montar_resultado_grafo(grafo, metricas_estrutura_coesao=None):
    """
    Monta o resultado completo de um grafo para ser usado pela view.

    Conteúdo retornado:
        - resumo do grafo
        - top-5 por centralidade
        - comunidades detectadas
        - métricas de estrutura/coesão previamente calculadas, se existirem

    Parâmetros:
        grafo (dict): grafo construído.
        metricas_estrutura_coesao (dict | None): métricas carregadas de outra etapa.

    Retorno:
        dict: resultado consolidado do grafo.
    """
    resumo = calcular_resumo_grafo(grafo)
    top_5 = obter_top_5_centralidade(grafo)
    comunidades = obter_resumo_comunidades(grafo, limite=5)

    nome_grafo = grafo["nome_grafo"]
    metricas_externas = None

    if metricas_estrutura_coesao and nome_grafo in metricas_estrutura_coesao:
        metricas_externas = metricas_estrutura_coesao[nome_grafo]

    return {
        "nome_grafo": nome_grafo,
        "resumo": resumo,
        "top_5_centralidade": top_5,
        "comunidades_detectadas": comunidades,
        "metricas_estrutura_coesao": metricas_externas
    }


def executar_backend(pasta_dados_processados=None, pasta_saida=None):
    """
    Interface programática principal do backend.

    Esta é a função mais importante para integração com uma possível GUI ou
    camada de visualização.

    Parâmetros:
        pasta_dados_processados (str | Path | None): pasta dos JSONs processados.
        pasta_saida (str | Path | None): pasta onde os resultados serão exportados.

    Retorno:
        dict: resultado completo com os quatro grafos.
    """
    pasta_raiz = localizar_pasta_raiz()

    if pasta_dados_processados is None:
        pasta_dados_processados = localizar_pasta_dados_processados(pasta_raiz)
    else:
        pasta_dados_processados = Path(pasta_dados_processados)

    if pasta_saida is None:
        pasta_saida = localizar_pasta_saida()
    else:
        pasta_saida = Path(pasta_saida)

    grafos = carregar_grafos_processados(pasta_dados_processados)
    metricas_estrutura_coesao = carregar_metricas_estrutura_coesao_se_existir(pasta_raiz)

    resultados_grafos = []

    ordem = ["comentarios", "fechamentos", "reviews_merges", "integrado"]
    for chave in ordem:
        resultado = montar_resultado_grafo(grafos[chave], metricas_estrutura_coesao)
        resultados_grafos.append(resultado)

    resultado_final = {
        "pasta_dados_processados": str(pasta_dados_processados),
        "pasta_saida": str(pasta_saida),
        "quantidade_grafos": len(resultados_grafos),
        "grafos": resultados_grafos
    }

    exportar_resultados(resultado_final, pasta_saida)

    return resultado_final



# EXPORTAÇÃO DOS RESULTADOS DO BACKEND


def criar_pasta(caminho):
    """
    Cria uma pasta caso ela ainda não exista.

    Parâmetros:
        caminho (str | Path): caminho da pasta.

    Retorno:
        Path: caminho criado/validado.
    """
    caminho = Path(caminho)
    caminho.mkdir(parents=True, exist_ok=True)
    return caminho


def arredondar(valor, casas=6):
    """
    Arredonda valores float para facilitar a leitura nas saídas.

    Parâmetros:
        valor (any): valor a ser arredondado.
        casas (int): quantidade de casas decimais.

    Retorno:
        any: valor arredondado, se for float; caso contrário, o próprio valor.
    """
    if isinstance(valor, float):
        return round(valor, casas)
    return valor


def preparar_para_json(objeto):
    """
    Converte estruturas não serializáveis em JSON para tipos simples.

    Exemplo:
        set -> list
        tuple -> list
        Path -> str

    Parâmetros:
        objeto (any): objeto a ser convertido.

    Retorno:
        any: objeto compatível com json.dump().
    """
    if isinstance(objeto, set):
        return sorted(list(objeto))

    if isinstance(objeto, tuple):
        return list(objeto)

    if isinstance(objeto, Path):
        return str(objeto)

    raise TypeError(f"Tipo não serializável: {type(objeto)}")


def exportar_resultados_json(resultado_final, caminho_saida):
    """
    Exporta o resultado completo em JSON.

    Parâmetros:
        resultado_final (dict): resultado gerado por executar_backend().
        caminho_saida (str | Path): caminho do arquivo JSON.
    """
    caminho_saida = Path(caminho_saida)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    with open(caminho_saida, "w", encoding="utf-8") as arquivo:
        json.dump(
            resultado_final,
            arquivo,
            ensure_ascii=False,
            indent=4,
            default=preparar_para_json
        )


def exportar_resumo_csv(resultado_final, caminho_saida):
    """
    Exporta o resumo dos grafos em CSV.

    Parâmetros:
        resultado_final (dict): resultado gerado por executar_backend().
        caminho_saida (str | Path): caminho do arquivo CSV.
    """
    caminho_saida = Path(caminho_saida)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    colunas = [
        "nome_grafo",
        "quantidade_vertices",
        "quantidade_arestas_direcionadas",
        "quantidade_arestas_nao_direcionadas",
        "peso_total_interacoes",
        "densidade_direcionada",
        "densidade_nao_direcionada"
    ]

    with open(caminho_saida, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, delimiter=";")
        escritor.writeheader()

        for resultado_grafo in resultado_final["grafos"]:
            resumo = resultado_grafo["resumo"]
            linha = {}
            for coluna in colunas:
                linha[coluna] = arredondar(resumo[coluna])
            escritor.writerow(linha)


def exportar_top5_csv(resultado_final, caminho_saida):
    """
    Exporta o Top-5 por centralidade de cada grafo em CSV.

    Parâmetros:
        resultado_final (dict): resultado gerado por executar_backend().
        caminho_saida (str | Path): caminho do arquivo CSV.
    """
    caminho_saida = Path(caminho_saida)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    colunas = [
        "nome_grafo",
        "posicao",
        "usuario",
        "grau_total",
        "centralidade_grau",
        "grau_entrada",
        "grau_saida",
        "grau_ponderado"
    ]

    with open(caminho_saida, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, delimiter=";")
        escritor.writeheader()

        for resultado_grafo in resultado_final["grafos"]:
            nome_grafo = resultado_grafo["nome_grafo"]
            for posicao, item in enumerate(resultado_grafo["top_5_centralidade"], start=1):
                linha = {
                    "nome_grafo": nome_grafo,
                    "posicao": posicao,
                    "usuario": item["usuario"],
                    "grau_total": item["grau_total"],
                    "centralidade_grau": arredondar(item["centralidade_grau"]),
                    "grau_entrada": item["grau_entrada"],
                    "grau_saida": item["grau_saida"],
                    "grau_ponderado": arredondar(item["grau_ponderado"])
                }
                escritor.writerow(linha)


def exportar_comunidades_csv(resultado_final, caminho_saida):
    """
    Exporta o resumo das comunidades detectadas em CSV.

    Parâmetros:
        resultado_final (dict): resultado gerado por executar_backend().
        caminho_saida (str | Path): caminho do arquivo CSV.
    """
    caminho_saida = Path(caminho_saida)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    colunas = [
        "nome_grafo",
        "id_comunidade",
        "tamanho",
        "amostra_membros"
    ]

    with open(caminho_saida, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, delimiter=";")
        escritor.writeheader()

        for resultado_grafo in resultado_final["grafos"]:
            nome_grafo = resultado_grafo["nome_grafo"]
            for comunidade in resultado_grafo["comunidades_detectadas"]:
                linha = {
                    "nome_grafo": nome_grafo,
                    "id_comunidade": comunidade["id_comunidade"],
                    "tamanho": comunidade["tamanho"],
                    "amostra_membros": ", ".join(comunidade["amostra_membros"])
                }
                escritor.writerow(linha)


def exportar_resultados(resultado_final, pasta_saida):
    """
    Exporta todos os arquivos de saída do backend.

    Arquivos gerados:
        - resultado_gui.json
        - resumo_grafos.csv
        - top5_centralidade.csv
        - comunidades_detectadas.csv

    Parâmetros:
        resultado_final (dict): resultado gerado por executar_backend().
        pasta_saida (str | Path): pasta de saída.
    """
    pasta_saida = criar_pasta(pasta_saida)

    exportar_resultados_json(resultado_final, pasta_saida / "resultado_gui.json")
    exportar_resumo_csv(resultado_final, pasta_saida / "resumo_grafos.csv")
    exportar_top5_csv(resultado_final, pasta_saida / "top5_centralidade.csv")
    exportar_comunidades_csv(resultado_final, pasta_saida / "comunidades_detectadas.csv")


if __name__ == "__main__":
    resultado = executar_backend()
    print("Backend executado com sucesso.")
    print(f"Grafos analisados: {resultado['quantidade_grafos']}")
    print(f"Arquivos gerados em: {resultado['pasta_saida']}")
