import json
import csv
from pathlib import Path


# ==========================================================
# MÉTRICAS DE ESTRUTURA E COESÃO
# 
# Este arquivo segue o padrão da pasta Metricas do projeto.
# Ele não usa bibliotecas de grafos, como NetworkX, igraph ou graph-tool.
# Toda a representação do grafo é feita com estruturas básicas do Python:
# dict, set, list e tuple.
#
# Métricas implementadas:
# 1. Densidade da rede
# 2. Coeficiente de aglomeração, clustering coefficient
# 3. Assortatividade por grau
#
# Grafos analisados:
# 1. Comentários em issues e PRs
# 2. Fechamentos de issues
# 3. Reviews, aprovações e merges
# 4. Integrado, combinação dos três anteriores
# ==========================================================

# LEITURA E NORMALIZAÇÃO DOS DADOS

def carregar_json(caminho_arquivo):
    """
    Lê um arquivo JSON contendo interações do repositório.

    Relação com grafos:
    - Cada registro do JSON representa uma possível aresta.
    - Os usuários presentes em origem e destino representam vértices.
    """
    caminho_arquivo = Path(caminho_arquivo)

    if not caminho_arquivo.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")

    with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def extrair_lista_registros(conteudo_json):
    """
    Extrai a lista de interações do JSON.

    Formato principal esperado:
    [
        {"de": "usuario_a", "para": "usuario_b", "peso": 3}
    ]

    Também aceita formatos em que a lista esteja dentro de uma chave,
    por exemplo: "arestas", "edges", "dados" ou "interacoes".
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
    Busca um campo no registro considerando nomes alternativos.

    Exemplo:
    - origem pode vir como "de", "origem", "source" ou "from".
    - destino pode vir como "para", "destino", "target" ou "to".
    """
    for nome in nomes_possiveis:
        if nome in registro:
            return registro[nome]
    return None


def converter_peso(valor):
    """
    Converte o peso da aresta para float.

    Relação com grafos:
    - O peso representa a intensidade da relação.
    - Exemplo: quantidade de comentários, fechamentos ou revisões.
    - Para densidade, clustering e assortatividade por grau, a existência da
      aresta é mais importante que o peso, mas o peso total é mantido no relatório.
    """
    if valor is None or valor == "":
        return 1.0

    try:
        return float(valor)
    except Exception:
        return 1.0


def normalizar_registro(registro):
    """
    Converte um registro bruto em uma aresta padronizada.

    Retorno:
    (origem, destino, peso)

    Relação com grafos:
    - origem e destino são vértices.
    - origem -> destino é uma aresta direcionada.
    - peso é a intensidade da interação.
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

def construir_grafo_direcionado(registros, ignorar_auto_lacos=True):
    """
    Constrói uma representação simples de grafo direcionado.

    Retorno:
    - vertices: conjunto de usuários
    - arestas_direcionadas: dicionário {(origem, destino): peso_total}

    Relação com grafos:
    - V é o conjunto de vértices.
    - E é o conjunto de arestas.
    - O grafo é direcionado porque a interação tem origem e destino.
    """
    vertices = set()
    arestas_direcionadas = {}

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

    return vertices, arestas_direcionadas


def converter_para_nao_direcionado(arestas_direcionadas):
    """
    Converte o grafo direcionado para uma versão não direcionada.

    Exemplo:
    A -> B e B -> A viram uma única conexão A -- B.

    Por que fazer isso?
    - Densidade pode ser calculada no grafo direcionado.
    - Clustering e assortatividade por grau costumam ser analisados na estrutura
      de vizinhança sem direção, principalmente para redes sociais/colaboração.
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

    Retorno:
    {
        vertice: {vizinho_1, vizinho_2, ...}
    }

    Relação com grafos:
    - Lista de adjacência é uma representação clássica de grafos.
    - Ela facilita calcular grau, vizinhança, clustering e assortatividade.
    """
    adjacencia = {}

    for vertice in vertices:
        adjacencia[vertice] = set()

    for origem, destino in arestas_nao_direcionadas:
        adjacencia.setdefault(origem, set()).add(destino)
        adjacencia.setdefault(destino, set()).add(origem)

    return adjacencia

# MÉTRICA 1: DENSIDADE DA REDE

def calcular_densidade_direcionada(vertices, arestas_direcionadas):
    """
    Calcula a densidade da rede considerando direção.

    Fórmula:
    densidade = m / (n * (n - 1))

    Onde:
    - n = número de vértices
    - m = número de arestas existentes
    - n * (n - 1) = número máximo de arestas direcionadas sem auto-laços

    Interpretação:
    - Próximo de 0: rede esparsa, poucos usuários interagem entre si.
    - Próximo de 1: rede muito conectada.
    """
    n = len(vertices)
    m = len(arestas_direcionadas)

    if n <= 1:
        return 0.0

    return m / (n * (n - 1))


def calcular_densidade_nao_direcionada(vertices, arestas_nao_direcionadas):
    """
    Calcula a densidade da rede sem considerar direção.

    Fórmula:
    densidade = m / (n * (n - 1) / 2)
    """
    n = len(vertices)
    m = len(arestas_nao_direcionadas)

    if n <= 1:
        return 0.0

    maximo_possivel = n * (n - 1) / 2
    return m / maximo_possivel

# MÉTRICA 2: COEFICIENTE DE AGLOMERAÇÃO

def calcular_coeficiente_aglomeracao(vertices, arestas_nao_direcionadas):
    """
    Calcula o clustering coefficient médio.

    Ideia:
    - Para cada vértice, observamos seus vizinhos.
    - Depois verificamos quantas conexões existem entre esses vizinhos.
    - Se os vizinhos também se conectam entre si, há formação de clusters.

    Fórmula local:
    C(v) = conexões existentes entre vizinhos / conexões possíveis entre vizinhos

    Retorno:
    - média considerando todos os vértices
    - média considerando apenas vértices com grau >= 2
    """
    adjacencia = montar_lista_adjacencia_nao_direcionada(vertices, arestas_nao_direcionadas)
    conjunto_arestas = set(arestas_nao_direcionadas.keys())

    valores_todos = []
    valores_grau_minimo_2 = []

    for vertice in vertices:
        vizinhos = list(adjacencia.get(vertice, set()))
        grau = len(vizinhos)

        if grau < 2:
            valores_todos.append(0.0)
            continue

        conexoes_existentes = 0

        for i in range(grau):
            for j in range(i + 1, grau):
                a = vizinhos[i]
                b = vizinhos[j]

                if a < b:
                    chave = (a, b)
                else:
                    chave = (b, a)

                if chave in conjunto_arestas:
                    conexoes_existentes += 1

        conexoes_possiveis = grau * (grau - 1) / 2
        coeficiente_local = conexoes_existentes / conexoes_possiveis

        valores_todos.append(coeficiente_local)
        valores_grau_minimo_2.append(coeficiente_local)

    if len(valores_todos) == 0:
        media_todos = 0.0
    else:
        media_todos = sum(valores_todos) / len(valores_todos)

    if len(valores_grau_minimo_2) == 0:
        media_grau_minimo_2 = 0.0
    else:
        media_grau_minimo_2 = sum(valores_grau_minimo_2) / len(valores_grau_minimo_2)

    return media_todos, media_grau_minimo_2

# MÉTRICA 3: ASSORTATIVIDADE POR GRAU

def calcular_assortatividade_por_grau(vertices, arestas_nao_direcionadas):
    """
    Calcula a assortatividade por grau.

    Ideia:
    - Verifica se vértices muito conectados tendem a se conectar com outros
      vértices muito conectados.

    Interpretação:
    - Valor positivo: tendência de conexão entre usuários de grau parecido.
    - Valor próximo de zero: não há padrão forte.
    - Valor negativo: usuários muito conectados tendem a se conectar com usuários
      menos conectados.

    Implementação:
    - Calcula a correlação entre os graus das extremidades das arestas.
    - Não usa nenhuma biblioteca de grafos ou estatística.
    """
    if len(arestas_nao_direcionadas) == 0:
        return None

    adjacencia = montar_lista_adjacencia_nao_direcionada(vertices, arestas_nao_direcionadas)

    graus = {}
    for vertice in vertices:
        graus[vertice] = len(adjacencia.get(vertice, set()))

    m = len(arestas_nao_direcionadas)

    soma_produto = 0.0
    soma_media_extremos = 0.0
    soma_media_quadrados_extremos = 0.0

    for origem, destino in arestas_nao_direcionadas:
        grau_origem = graus[origem]
        grau_destino = graus[destino]

        soma_produto += grau_origem * grau_destino
        soma_media_extremos += 0.5 * (grau_origem + grau_destino)
        soma_media_quadrados_extremos += 0.5 * ((grau_origem ** 2) + (grau_destino ** 2))

    termo1 = soma_produto / m
    termo2 = (soma_media_extremos / m) ** 2
    termo3 = soma_media_quadrados_extremos / m

    denominador = termo3 - termo2

    if abs(denominador) < 0.0000000001:
        return None

    return (termo1 - termo2) / denominador

# INTERPRETAÇÕES

def classificar_metrica_zero_um(valor):
    """
    Classificação simples para métricas que variam entre 0 e 1.
    """
    if valor is None:
        return "indefinido"

    if valor < 0.01:
        return "muito baixo"
    if valor < 0.05:
        return "baixo"
    if valor < 0.15:
        return "moderado"
    if valor < 0.35:
        return "alto"
    return "muito alto"


def interpretar_assortatividade(valor):
    """
    Interpreta o valor de assortatividade por grau.
    """
    if valor is None:
        return "indefinida, pois não há arestas ou não há variação suficiente nos graus"

    if valor > 0.20:
        return "positiva: colaboradores muito conectados tendem a se conectar entre si"
    if valor > 0.05:
        return "levemente positiva: existe alguma tendência de conexão entre colaboradores com graus semelhantes"
    if valor >= -0.05:
        return "próxima de zero: não há padrão forte de conexão por grau"
    if valor >= -0.20:
        return "levemente negativa: colaboradores muito conectados tendem a interagir um pouco mais com menos conectados"
    return "negativa: colaboradores muito conectados tendem a interagir com colaboradores menos conectados"


# ANÁLISE DE UM GRAFO

def analisar_estrutura_coesao_grafo(nome_grafo, registros):
    """
    Executa as métricas de estrutura e coesão para um grafo.

    Métricas calculadas:
    - densidade da rede
    - clustering coefficient
    - assortatividade por grau
    """
    vertices, arestas_direcionadas = construir_grafo_direcionado(registros)
    arestas_nao_direcionadas = converter_para_nao_direcionado(arestas_direcionadas)

    densidade_direcionada = calcular_densidade_direcionada(vertices, arestas_direcionadas)
    densidade_nao_direcionada = calcular_densidade_nao_direcionada(vertices, arestas_nao_direcionadas)

    clustering_todos, clustering_grau_minimo_2 = calcular_coeficiente_aglomeracao(
        vertices,
        arestas_nao_direcionadas
    )

    assortatividade = calcular_assortatividade_por_grau(vertices, arestas_nao_direcionadas)
    peso_total = sum(arestas_direcionadas.values())

    return {
        "nome_grafo": nome_grafo,
        "quantidade_vertices": len(vertices),
        "quantidade_arestas_direcionadas": len(arestas_direcionadas),
        "quantidade_arestas_nao_direcionadas": len(arestas_nao_direcionadas),
        "peso_total_interacoes": peso_total,
        "densidade_direcionada": densidade_direcionada,
        "densidade_nao_direcionada": densidade_nao_direcionada,
        "coeficiente_aglomeracao_medio_todos_vertices": clustering_todos,
        "coeficiente_aglomeracao_medio_grau_maior_igual_2": clustering_grau_minimo_2,
        "assortatividade_por_grau": assortatividade,
        "interpretacao_densidade": classificar_metrica_zero_um(densidade_direcionada),
        "interpretacao_aglomeracao": classificar_metrica_zero_um(clustering_todos),
        "interpretacao_assortatividade": interpretar_assortatividade(assortatividade)
    }

# SAÍDAS

def criar_pasta_saida(pasta_saida):
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    return pasta_saida


def arredondar_valor(valor, casas=6):
    if valor is None:
        return ""

    if isinstance(valor, float):
        return round(valor, casas)

    return valor


def salvar_json(resultados, caminho_saida):
    caminho_saida = Path(caminho_saida)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    with open(caminho_saida, "w", encoding="utf-8") as arquivo:
        json.dump(resultados, arquivo, ensure_ascii=False, indent=4)


def salvar_csv(resultados, caminho_saida):
    caminho_saida = Path(caminho_saida)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    colunas = [
        "nome_grafo",
        "quantidade_vertices",
        "quantidade_arestas_direcionadas",
        "quantidade_arestas_nao_direcionadas",
        "peso_total_interacoes",
        "densidade_direcionada",
        "densidade_nao_direcionada",
        "coeficiente_aglomeracao_medio_todos_vertices",
        "coeficiente_aglomeracao_medio_grau_maior_igual_2",
        "assortatividade_por_grau",
        "interpretacao_densidade",
        "interpretacao_aglomeracao",
        "interpretacao_assortatividade"
    ]

    with open(caminho_saida, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, delimiter=";")
        escritor.writeheader()

        for resultado in resultados:
            linha = {}
            for coluna in colunas:
                linha[coluna] = arredondar_valor(resultado[coluna])
            escritor.writerow(linha)


def salvar_relatorio_txt(resultados, caminho_saida):
    caminho_saida = Path(caminho_saida)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    linhas = []
    linhas.append("MÉTRICAS DE ESTRUTURA E COESÃO")
    linhas.append("=" * 70)
    linhas.append("")
    linhas.append("Métricas calculadas sem bibliotecas de grafos.")
    linhas.append("Representação interna utilizada: conjuntos e dicionários do Python.")
    linhas.append("")
    linhas.append("Métricas:")
    linhas.append("1. Densidade da rede")
    linhas.append("2. Coeficiente de aglomeração, clustering coefficient")
    linhas.append("3. Assortatividade por grau")
    linhas.append("")
    linhas.append("Observação:")
    linhas.append("- A densidade direcionada considera origem -> destino.")
    linhas.append("- O clustering e a assortatividade foram calculados na versão não direcionada do grafo.")
    linhas.append("")

    for resultado in resultados:
        linhas.append("-" * 70)
        linhas.append(resultado["nome_grafo"])
        linhas.append("-" * 70)
        linhas.append(f"Vértices: {resultado['quantidade_vertices']}")
        linhas.append(f"Arestas direcionadas: {resultado['quantidade_arestas_direcionadas']}")
        linhas.append(f"Arestas não direcionadas: {resultado['quantidade_arestas_nao_direcionadas']}")
        linhas.append(f"Peso total das interações: {round(resultado['peso_total_interacoes'], 6)}")
        linhas.append(f"Densidade direcionada: {round(resultado['densidade_direcionada'], 6)}")
        linhas.append(f"Densidade não direcionada: {round(resultado['densidade_nao_direcionada'], 6)}")
        linhas.append(f"Coeficiente de aglomeração médio, todos os vértices: {round(resultado['coeficiente_aglomeracao_medio_todos_vertices'], 6)}")
        linhas.append(f"Coeficiente de aglomeração médio, grau >= 2: {round(resultado['coeficiente_aglomeracao_medio_grau_maior_igual_2'], 6)}")

        if resultado["assortatividade_por_grau"] is None:
            linhas.append("Assortatividade por grau: indefinida")
        else:
            linhas.append(f"Assortatividade por grau: {round(resultado['assortatividade_por_grau'], 6)}")

        linhas.append(f"Interpretação da densidade: {resultado['interpretacao_densidade']}")
        linhas.append(f"Interpretação da aglomeração: {resultado['interpretacao_aglomeracao']}")
        linhas.append(f"Interpretação da assortatividade: {resultado['interpretacao_assortatividade']}")
        linhas.append("")

    with open(caminho_saida, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas))

# ANÁLISE DOS 4 GRAFOS

def carregar_registros_dos_grafos(pasta_dados_processados):
    """
    Carrega os três arquivos de entrada e monta também o grafo integrado.
    """
    pasta_dados_processados = Path(pasta_dados_processados)

    arquivos = {
        "Grafo 1 - Comentários em issues e PRs": pasta_dados_processados / "comentarios.json",
        "Grafo 2 - Fechamentos de issues": pasta_dados_processados / "fechamentos.json",
        "Grafo 3 - Reviews, aprovações e merges": pasta_dados_processados / "reviews_merges.json"
    }

    registros_por_grafo = {}

    for nome_grafo, caminho_arquivo in arquivos.items():
        conteudo_json = carregar_json(caminho_arquivo)
        registros_por_grafo[nome_grafo] = extrair_lista_registros(conteudo_json)

    registros_integrados = []

    for nome_grafo in registros_por_grafo:
        registros_integrados.extend(registros_por_grafo[nome_grafo])

    registros_por_grafo["Grafo 4 - Integrado"] = registros_integrados

    return registros_por_grafo


def analisar_quatro_grafos_estrutura_coesao(pasta_dados_processados, pasta_saida):
    """
    Função principal desta história.

    Executa as métricas de estrutura e coesão nos 4 grafos esperados.
    """
    pasta_saida = criar_pasta_saida(pasta_saida)

    registros_por_grafo = carregar_registros_dos_grafos(pasta_dados_processados)

    resultados = []

    for nome_grafo, registros in registros_por_grafo.items():
        resultado = analisar_estrutura_coesao_grafo(nome_grafo, registros)
        resultados.append(resultado)

    salvar_json(resultados, pasta_saida / "metricas_estrutura_coesao.json")
    salvar_csv(resultados, pasta_saida / "metricas_estrutura_coesao.csv")
    salvar_relatorio_txt(resultados, pasta_saida / "relatorio_estrutura_coesao.txt")

    return resultados

# LOCALIZAÇÃO AUTOMÁTICA DE PASTAS

def localizar_pasta_dados_processados():
    """
    Localiza automaticamente a pasta de dados processados.

    Estrutura principal esperada:
    Projeto/
    ├── ExtracaoDados/
    │   └── dados_processados/
    └── Metricas/
        └── MetricasDeEstruturaCoesao.py
    """
    pasta_atual = Path(__file__).resolve().parent
    pasta_raiz = pasta_atual.parent

    opcoes = [
        pasta_raiz / "ExtracaoDados" / "dados_processados",
        pasta_raiz / "ExtracaoDados" / "DadosProcessados",
        pasta_raiz / "dados_processados",
        pasta_atual / "dados_processados"
    ]

    for opcao in opcoes:
        if opcao.exists():
            return opcao

    raise FileNotFoundError(
        "Não encontrei a pasta de dados processados. "
        "Verifique se existe: ExtracaoDados/dados_processados"
    )


def localizar_pasta_saida():
    """
    Define a pasta de saída das métricas dentro da própria pasta Metricas.
    """
    pasta_atual = Path(__file__).resolve().parent
    return pasta_atual / "saida_metricas" / "estrutura_coesao"

# EXECUÇÃO DIRETA

if __name__ == "__main__":
    pasta_dados_processados = localizar_pasta_dados_processados()
    pasta_saida = localizar_pasta_saida()

    print("Iniciando métricas de estrutura e coesão...")
    print(f"Pasta de dados processados: {pasta_dados_processados}")
    print(f"Pasta de saída: {pasta_saida}")
    print()

    resultados = analisar_quatro_grafos_estrutura_coesao(
        pasta_dados_processados=pasta_dados_processados,
        pasta_saida=pasta_saida
    )

    for resultado in resultados:
        print(resultado["nome_grafo"])
        print(f"  Vértices: {resultado['quantidade_vertices']}")
        print(f"  Arestas direcionadas: {resultado['quantidade_arestas_direcionadas']}")
        print(f"  Densidade direcionada: {resultado['densidade_direcionada']:.6f}")
        print(f"  Clustering médio: {resultado['coeficiente_aglomeracao_medio_todos_vertices']:.6f}")

        if resultado["assortatividade_por_grau"] is None:
            print("  Assortatividade: indefinida")
        else:
            print(f"  Assortatividade: {resultado['assortatividade_por_grau']:.6f}")

        print()

    print("Métricas de estrutura e coesão concluídas.")
    print("Arquivos gerados:")
    print(f"  {pasta_saida / 'metricas_estrutura_coesao.json'}")
    print(f"  {pasta_saida / 'metricas_estrutura_coesao.csv'}")
    print(f"  {pasta_saida / 'relatorio_estrutura_coesao.txt'}")
