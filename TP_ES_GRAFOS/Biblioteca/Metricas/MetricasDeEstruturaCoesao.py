import json
import csv
from pathlib import Path



# MÉTRICAS DE ESTRUTURA E COESÃO
# 
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


# LEITURA E NORMALIZAÇÃO DOS DADOS

def carregar_json(caminho_arquivo):
    """
    Carrega e retorna o conteúdo de um arquivo JSON.

    Parâmetros:
        caminho_arquivo (str | pathlib.Path):
            Caminho do arquivo JSON que contém os dados de interação do repositório.

    Retorno:
        list | dict:
            Conteúdo do JSON já convertido para estruturas nativas do Python.

    Exceções:
        FileNotFoundError:
            Gerada quando o arquivo informado não existe.

    Relação com grafos:
        Nesta etapa, cada registro do JSON pode representar uma aresta do grafo.
        Os usuários encontrados nos campos de origem e destino formarão o conjunto
        de vértices V, enquanto as interações formarão o conjunto de arestas E.
    """
    caminho_arquivo = Path(caminho_arquivo)

    if not caminho_arquivo.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")

    with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def extrair_lista_registros(conteudo_json):
    """
    Extrai a lista de registros de interação a partir do conteúdo carregado do JSON.

    Parâmetros:
        conteudo_json (list | dict):
            Conteúdo retornado por carregar_json. Pode ser diretamente uma lista
            de registros ou um dicionário contendo a lista em uma chave conhecida.

    Retorno:
        list:
            Lista de registros de interação que serão convertidos em arestas.

    Formatos aceitos:
        1. Lista direta:
            [
                {"de": "usuario_a", "para": "usuario_b", "peso": 3}
            ]

        2. Dicionário contendo a lista em uma das chaves:
            "arestas", "edges", "dados", "interacoes", "registros" ou "items".

    Exceções:
        ValueError:
            Gerada quando o conteúdo não possui um formato reconhecido.

    Relação com grafos:
        Esta função prepara os dados brutos para a construção do conjunto de arestas E.
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
    Busca o valor de um campo em um registro, aceitando nomes alternativos.

    Parâmetros:
        registro (dict):
            Registro individual de interação.
        nomes_possiveis (list[str]):
            Lista de nomes possíveis para o campo desejado.

    Retorno:
        any | None:
            Valor encontrado no primeiro nome existente dentro do registro.
            Retorna None caso nenhum dos nomes seja encontrado.

    Exemplo:
        Para origem, podem ser testados nomes como:
        "de", "origem", "source", "from", "autor" e "user_from".

    Objetivo:
        Permitir que o código funcione mesmo que os arquivos JSON usem nomes
        diferentes para representar origem, destino ou peso.

    Relação com grafos:
        Ajuda a identificar os dois vértices extremos de uma aresta:
        origem e destino.
    """
    for nome in nomes_possiveis:
        if nome in registro:
            return registro[nome]
    return None


def converter_peso(valor):
    """
    Converte o peso de uma interação para float.

    Parâmetros:
        valor (any):
            Valor bruto do peso vindo do JSON. Pode ser número, texto numérico,
            vazio ou None.

    Retorno:
        float:
            Peso convertido. Caso o valor esteja vazio ou inválido, retorna 1.0.

    Relação com grafos:
        O peso representa a intensidade da aresta. No contexto do GitHub, ele pode
        indicar, por exemplo, quantidade de comentários, fechamentos, revisões,
        aprovações ou merges entre dois usuários.

    Observação:
        Para as métricas de densidade, clustering e assortatividade por grau, o
        cálculo principal usa a existência da aresta. Mesmo assim, o peso é mantido
        para relatório e análise da intensidade total das interações.
    """
    if valor is None or valor == "":
        return 1.0

    try:
        return float(valor)
    except Exception:
        return 1.0


def normalizar_registro(registro):
    """
    Converte um registro bruto do JSON em uma aresta padronizada.

    Parâmetros:
        registro (dict):
            Registro de interação contendo origem, destino e, opcionalmente, peso.

    Retorno:
        tuple[str, str, float]:
            Tupla no formato:
            (origem, destino, peso)

    Exceções:
        ValueError:
            Gerada quando o registro não é um dicionário, não possui origem/destino
            ou contém origem/destino vazios.

    Relação com grafos:
        A função transforma um dado bruto em uma aresta direcionada:
            origem -> destino

        Origem e destino são vértices do grafo, e o peso representa a intensidade
        da relação entre esses dois vértices.
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
    Constrói uma representação interna de grafo direcionado a partir dos registros.

    Parâmetros:
        registros (list[dict]):
            Lista de registros de interação.
        ignorar_auto_lacos (bool):
            Quando True, remove arestas em que origem e destino são o mesmo usuário.
            Essas arestas são chamadas de auto-laços.

    Retorno:
        tuple[set, dict]:
            vertices:
                Conjunto com todos os usuários encontrados.
            arestas_direcionadas:
                Dicionário no formato:
                {
                    (origem, destino): peso_total
                }

    Funcionamento:
        - Cada registro é normalizado para (origem, destino, peso).
        - Origem e destino são adicionados ao conjunto de vértices.
        - A aresta (origem, destino) recebe o peso acumulado.
        - Se a mesma aresta aparecer mais de uma vez, os pesos são somados.

    Relação com grafos:
        Implementa a construção de G = (V, E), onde:
        - V é o conjunto de vértices.
        - E é o conjunto de arestas direcionadas.
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
    Converte as arestas direcionadas em uma representação não direcionada.

    Parâmetros:
        arestas_direcionadas (dict):
            Dicionário de arestas direcionadas no formato:
            {
                (origem, destino): peso_total
            }

    Retorno:
        dict:
            Dicionário de arestas não direcionadas no formato:
            {
                (vertice_a, vertice_b): peso_total
            }

    Funcionamento:
        - Arestas A -> B e B -> A passam a representar uma única conexão A -- B.
        - Os pesos das duas direções são somados.
        - A ordem dos vértices na chave é padronizada para evitar duplicidade.

    Por que isso é feito:
        Algumas métricas de coesão e estrutura social, como clustering coefficient
        e assortatividade por grau, costumam ser analisadas considerando apenas se
        dois colaboradores estão conectados, sem diferenciar a direção da interação.

    Relação com grafos:
        Transforma um grafo direcionado em uma versão não direcionada para cálculo
        de métricas baseadas em vizinhança.
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
    Monta a lista de adjacência de um grafo não direcionado.

    Parâmetros:
        vertices (set):
            Conjunto de vértices do grafo.
        arestas_nao_direcionadas (dict):
            Dicionário de arestas não direcionadas.

    Retorno:
        dict[str, set]:
            Dicionário no formato:
            {
                vertice: {vizinho_1, vizinho_2, ...}
            }

    Funcionamento:
        Para cada aresta A -- B:
        - B é adicionado como vizinho de A.
        - A é adicionado como vizinho de B.

    Relação com grafos:
        A lista de adjacência é uma representação clássica de grafos. Ela facilita
        o cálculo de grau, vizinhança, clustering coefficient e assortatividade.
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
    Calcula a densidade da rede considerando as arestas direcionadas.

    Parâmetros:
        vertices (set):
            Conjunto de vértices do grafo.
        arestas_direcionadas (dict):
            Dicionário de arestas direcionadas.

    Retorno:
        float:
            Valor da densidade direcionada no intervalo entre 0 e 1.

    Fórmula:
        densidade = m / (n * (n - 1))

    Onde:
        n = número de vértices.
        m = número de arestas direcionadas existentes.
        n * (n - 1) = número máximo de arestas direcionadas sem auto-laços.

    Interpretação:
        - Valor próximo de 0: rede esparsa, com poucas conexões.
        - Valor próximo de 1: rede muito conectada.

    Relação com grafos:
        Mede a proporção de arestas existentes em relação ao número máximo possível
        de arestas em um grafo direcionado.
    """
    n = len(vertices)
    m = len(arestas_direcionadas)

    if n <= 1:
        return 0.0

    return m / (n * (n - 1))


def calcular_densidade_nao_direcionada(vertices, arestas_nao_direcionadas):
    """
    Calcula a densidade da rede sem considerar a direção das arestas.

    Parâmetros:
        vertices (set):
            Conjunto de vértices do grafo.
        arestas_nao_direcionadas (dict):
            Dicionário de arestas não direcionadas.

    Retorno:
        float:
            Valor da densidade não direcionada no intervalo entre 0 e 1.

    Fórmula:
        densidade = m / (n * (n - 1) / 2)

    Onde:
        n = número de vértices.
        m = número de arestas não direcionadas existentes.
        n * (n - 1) / 2 = número máximo de conexões sem direção.

    Relação com grafos:
        Indica o quanto a rede está conectada quando a direção das interações é
        ignorada.
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
    Calcula o coeficiente de aglomeração médio do grafo.

    Parâmetros:
        vertices (set):
            Conjunto de vértices do grafo.
        arestas_nao_direcionadas (dict):
            Dicionário de arestas não direcionadas.

    Retorno:
        tuple[float, float]:
            media_todos:
                Média do coeficiente local considerando todos os vértices.
                Vértices com grau menor que 2 entram com valor 0.
            media_grau_minimo_2:
                Média considerando apenas vértices com grau maior ou igual a 2.

    Ideia:
        Para cada vértice, o algoritmo verifica se seus vizinhos também estão
        conectados entre si. Quando isso ocorre com frequência, há formação de
        grupos locais ou clusters.

    Fórmula local:
        C(v) = conexões existentes entre vizinhos de v /
               conexões possíveis entre vizinhos de v

    Relação com grafos:
        Mede a tendência de formação de triângulos e pequenos grupos densos na rede.
        Em uma rede de colaboração, valores maiores podem indicar comunidades de
        colaboradores que interagem fortemente entre si.
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
    Calcula a assortatividade por grau do grafo.

    Parâmetros:
        vertices (set):
            Conjunto de vértices do grafo.
        arestas_nao_direcionadas (dict):
            Dicionário de arestas não direcionadas.

    Retorno:
        float | None:
            Coeficiente de assortatividade por grau.
            Retorna None quando a métrica não pode ser calculada, por exemplo,
            quando não há arestas ou quando não existe variação suficiente nos graus.

    Ideia:
        A métrica verifica se vértices com muitos vizinhos tendem a se conectar com
        outros vértices também muito conectados.

    Interpretação:
        - Valor positivo:
            colaboradores muito conectados tendem a se conectar entre si.
        - Valor próximo de zero:
            não há padrão forte de conexão por grau.
        - Valor negativo:
            colaboradores muito conectados tendem a se conectar com colaboradores
            menos conectados.

    Implementação:
        O cálculo é feito por meio da correlação entre os graus dos dois extremos
        de cada aresta, sem usar bibliotecas de grafos ou estatística.
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
    Classifica qualitativamente uma métrica cujo valor varia entre 0 e 1.

    Parâmetros:
        valor (float | None):
            Valor numérico da métrica.

    Retorno:
        str:
            Classificação textual:
            "indefinido", "muito baixo", "baixo", "moderado", "alto" ou "muito alto".

    Uso no código:
        É aplicada principalmente para interpretar densidade e coeficiente de
        aglomeração.

    Observação:
        Os limites usados são heurísticos e servem para facilitar a leitura do
        relatório. Dependendo do tamanho e tipo da rede, a interpretação pode ser
        ajustada.
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
    Gera uma interpretação textual para a assortatividade por grau.

    Parâmetros:
        valor (float | None):
            Valor calculado da assortatividade por grau.

    Retorno:
        str:
            Texto explicativo sobre o padrão de conexão da rede.

    Interpretação:
        - Positiva:
            usuários muito conectados tendem a interagir com outros muito conectados.
        - Próxima de zero:
            não há padrão forte de conexão por grau.
        - Negativa:
            usuários muito conectados tendem a interagir com usuários menos conectados.

    Objetivo:
        Facilitar o uso dos resultados no relatório final do trabalho, evitando que
        apenas o número seja apresentado sem explicação.
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
    Executa todas as métricas de estrutura e coesão para um grafo específico.

    Parâmetros:
        nome_grafo (str):
            Nome descritivo do grafo analisado.
        registros (list[dict]):
            Lista de registros de interação correspondente ao grafo.

    Retorno:
        dict:
            Dicionário contendo:
            - nome do grafo;
            - quantidade de vértices;
            - quantidade de arestas direcionadas;
            - quantidade de arestas não direcionadas;
            - peso total das interações;
            - densidade direcionada;
            - densidade não direcionada;
            - coeficiente de aglomeração médio;
            - assortatividade por grau;
            - interpretações textuais das métricas.

    Fluxo:
        1. Constrói o grafo direcionado.
        2. Converte o grafo para não direcionado.
        3. Calcula densidade.
        4. Calcula clustering coefficient.
        5. Calcula assortatividade por grau.
        6. Monta um dicionário final com resultados e interpretações.

    Relação com grafos:
        Esta função centraliza a análise de G = (V, E) para um dos quatro grafos
        do trabalho.
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
    """
    Cria a pasta de saída, caso ela ainda não exista.

    Parâmetros:
        pasta_saida (str | pathlib.Path):
            Caminho onde os arquivos de resultado serão salvos.

    Retorno:
        pathlib.Path:
            Caminho da pasta de saída convertido para Path.

    Objetivo:
        Garantir que os arquivos JSON, CSV e TXT possam ser salvos sem erro de
        diretório inexistente.

    Relação com grafos:
        Não calcula métrica de grafo. É uma função auxiliar de organização da saída.
    """
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    return pasta_saida


def arredondar_valor(valor, casas=6):
    """
    Arredonda valores numéricos para facilitar a escrita em arquivos de saída.

    Parâmetros:
        valor (any):
            Valor a ser tratado.
        casas (int):
            Quantidade de casas decimais desejada para números float.

    Retorno:
        any:
            - String vazia quando o valor é None.
            - Float arredondado quando o valor é float.
            - Valor original nos demais casos.

    Objetivo:
        Evitar que o CSV fique com números muito longos e melhorar a legibilidade
        dos resultados.
    """
    if valor is None:
        return ""

    if isinstance(valor, float):
        return round(valor, casas)

    return valor


def salvar_json(resultados, caminho_saida):
    """
    Salva os resultados das métricas em um arquivo JSON.

    Parâmetros:
        resultados (list[dict]):
            Lista com os resultados calculados para os grafos.
        caminho_saida (str | pathlib.Path):
            Caminho completo do arquivo JSON que será gerado.

    Retorno:
        None

    Objetivo:
        Gerar uma saída estruturada que possa ser reutilizada por outros scripts ou
        consultada posteriormente.

    Formato:
        O arquivo é salvo com indentação e com suporte a acentos por meio de
        ensure_ascii=False.
    """
    caminho_saida = Path(caminho_saida)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    with open(caminho_saida, "w", encoding="utf-8") as arquivo:
        json.dump(resultados, arquivo, ensure_ascii=False, indent=4)


def salvar_csv(resultados, caminho_saida):
    """
    Salva os resultados das métricas em um arquivo CSV separado por ponto e vírgula.

    Parâmetros:
        resultados (list[dict]):
            Lista com os resultados calculados para cada grafo.
        caminho_saida (str | pathlib.Path):
            Caminho completo do arquivo CSV que será gerado.

    Retorno:
        None

    Objetivo:
        Criar uma tabela simples para análise, comparação entre os quatro grafos e
        possível inclusão no relatório do trabalho.

    Observação:
        O delimitador usado é ";", pois esse formato costuma abrir melhor em Excel
        configurado em português.
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
    """
    Gera um relatório textual com as métricas e interpretações.

    Parâmetros:
        resultados (list[dict]):
            Lista com os resultados das análises.
        caminho_saida (str | pathlib.Path):
            Caminho completo do arquivo TXT que será gerado.

    Retorno:
        None

    Conteúdo gerado:
        - Título da análise.
        - Explicação das métricas.
        - Observações sobre direção das arestas.
        - Resultados individuais dos quatro grafos.
        - Interpretações textuais de densidade, aglomeração e assortatividade.

    Objetivo:
        Produzir uma saída legível para ser usada como base na escrita do relatório
        acadêmico.
    """
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
    Carrega os registros dos três arquivos processados e monta o grafo integrado.

    Parâmetros:
        pasta_dados_processados (str | pathlib.Path):
            Pasta que contém os arquivos:
            - comentarios.json
            - fechamentos.json
            - reviews_merges.json

    Retorno:
        dict[str, list]:
            Dicionário no formato:
            {
                nome_do_grafo: lista_de_registros
            }

    Grafos carregados:
        1. Grafo de comentários em issues e PRs.
        2. Grafo de fechamentos de issues.
        3. Grafo de reviews, aprovações e merges.
        4. Grafo integrado, formado pela união dos registros dos três anteriores.

    Relação com grafos:
        Define quais conjuntos de arestas serão analisados em cada grafo.
        O grafo integrado combina as interações para representar uma visão geral
        da colaboração no repositório.
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
    Executa a análise de estrutura e coesão para os quatro grafos do trabalho.

    Parâmetros:
        pasta_dados_processados (str | pathlib.Path):
            Pasta onde estão os arquivos JSON processados.
        pasta_saida (str | pathlib.Path):
            Pasta onde serão salvos os arquivos de resultado.

    Retorno:
        list[dict]:
            Lista com o resultado das métricas para cada grafo.

    Arquivos gerados:
        - metricas_estrutura_coesao.json
        - metricas_estrutura_coesao.csv
        - relatorio_estrutura_coesao.txt

    Fluxo:
        1. Cria a pasta de saída.
        2. Carrega os registros dos quatro grafos.
        3. Calcula as métricas de cada grafo.
        4. Salva os resultados em JSON, CSV e TXT.

    Relação com a história:
        Esta é a função principal da história de métricas de estrutura e coesão.
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
    Localiza automaticamente a pasta de dados processados do projeto.

    Parâmetros:
        Nenhum.

    Retorno:
        pathlib.Path:
            Caminho encontrado para a pasta de dados processados.

    Estrutura esperada principal:
        Projeto/
        ├── ExtracaoDados/
        │   └── dados_processados/
        └── Metricas/
            └── MetricasDeEstruturaCoesao.py

    Pastas alternativas verificadas:
        - ExtracaoDados/dados_processados
        - ExtracaoDados/DadosProcessados
        - dados_processados
        - Metricas/dados_processados

    Exceções:
        FileNotFoundError:
            Gerada quando nenhuma das opções esperadas é encontrada.

    Objetivo:
        Permitir que o script seja executado diretamente sem exigir que o usuário
        informe caminhos manualmente.
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
    Define automaticamente a pasta onde os resultados serão salvos.

    Parâmetros:
        Nenhum.

    Retorno:
        pathlib.Path:
            Caminho da pasta:
            Metricas/saida_metricas/estrutura_coesao

    Objetivo:
        Manter os resultados desta história organizados dentro da pasta Metricas,
        seguindo o padrão das demais métricas do projeto.
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
