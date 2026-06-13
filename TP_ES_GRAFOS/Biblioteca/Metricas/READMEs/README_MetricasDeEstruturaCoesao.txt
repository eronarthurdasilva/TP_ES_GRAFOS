Arquivo ajustado para seguir o padrão da pasta Metricas.

Coloque o arquivo abaixo dentro da pasta Metricas do projeto:

Metricas/MetricasDeEstruturaCoesao.py

Estrutura esperada:

Projeto/
├── ExtracaoDados/
│   └── dados_processados/
│       ├── comentarios.json
│       ├── fechamentos.json
│       └── reviews_merges.json
└── Metricas/
    ├── MetricasDeCentralidade.py
    ├── MetricasDeComunidade.py
    └── MetricasDeEstruturaCoesao.py

Para rodar a partir da raiz do projeto:

python Metricas/MetricasDeEstruturaCoesao.py

Ou no Windows:

py Metricas/MetricasDeEstruturaCoesao.py

Saídas geradas:

Metricas/saida_metricas/estrutura_coesao/
├── metricas_estrutura_coesao.json
├── metricas_estrutura_coesao.csv
└── relatorio_estrutura_coesao.txt

Observação:
O código não usa nenhuma biblioteca de grafos. Usa apenas bibliotecas padrão do Python.
