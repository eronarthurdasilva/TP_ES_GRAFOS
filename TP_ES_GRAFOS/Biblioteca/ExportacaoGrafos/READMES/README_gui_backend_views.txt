GUI BACKEND E GUI VIEWS - EXPORTAÇÃO/ANÁLISE DOS GRAFOS
========================================================

Arquivos adicionados:

1. gui_backend.py
   Backend programático que conecta os dados dos grafos com as métricas.
   Ele carrega os JSONs processados, constrói os grafos internamente, calcula
   resumo do grafo, Top-5 por centralidade, comunidades detectadas e exporta
   os resultados em CSV/JSON.

2. gui_views.py
   Camada de saída textual. Mostra no terminal tabelas formatadas com:
   - resumo do grafo;
   - Top-5 por centralidade;
   - comunidades detectadas;
   - métricas de estrutura/coesão, se já tiverem sido geradas na pasta Metricas.

3. RodarInterfaceGrafos.py
   Arquivo simples para executar o backend + views.

COMO RODAR
----------

A estrutura esperada é:

Projeto/
├── ExtracaoDados/
│   └── dados_processados/
│       ├── comentarios.json
│       ├── fechamentos.json
│       └── reviews_merges.json
├── Metricas/
│   └── saida_metricas/
│       └── estrutura_coesao/
│           └── metricas_estrutura_coesao.json   (opcional)
└── ExportacaoGrafos/
    ├── gui_backend.py
    ├── gui_views.py
    └── RodarInterfaceGrafos.py

Execute:

python ExportacaoGrafos/RodarInterfaceGrafos.py

SAÍDAS GERADAS
--------------

Os arquivos serão gerados em:

ExportacaoGrafos/saida_gui/

Arquivos:

- resultado_gui.json
- resumo_grafos.csv
- top5_centralidade.csv
- comunidades_detectadas.csv

OBSERVAÇÃO
----------

Nenhum arquivo usa bibliotecas de grafos como NetworkX, igraph ou graph-tool.
A implementação usa apenas estruturas nativas do Python.
