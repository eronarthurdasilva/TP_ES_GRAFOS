ExportacaoGrafos
================

Esta pasta exporta os 4 grafos do trabalho para o formato .gexf, aceito pelo Gephi.

Não usa biblioteca de grafos.
Usa apenas Python puro com dict, list, json e escrita de arquivo texto/XML.

Arquivos principais
-------------------

ExportacaoGexf.py
    Código principal de exportação.

RodarExportacao.py
    Roda a exportação com os dados reais do projeto.

RodarExemploLocal.py
    Roda uma exportação pequena com dados de exemplo.
    Este exemplo TEM arestas.

ConferirGexf.py
    Conta quantos vértices e arestas existem em um arquivo .gexf.

Como rodar com os dados reais
-----------------------------

A estrutura esperada é:

Projeto/
├── ConstrucaoGrafos/
│   └── mapeamento_vertices.json
├── ExtracaoDados/
│   └── dados_processados/
│       ├── comentarios.json
│       ├── fechamentos.json
│       └── reviews_merges.json
└── ExportacaoGrafos/

A partir da raiz do projeto:

python ConstrucaoGrafos/MapeamentoVertices.py
python ConstrucaoGrafos/Construcao.py
python ExportacaoGrafos/RodarExportacao.py

Saída esperada
--------------

ExportacaoGrafos/saida_gexf/
├── grafo_1_comentarios.gexf
├── grafo_2_fechamentos.gexf
├── grafo_3_reviews_merges.gexf
└── grafo_4_integrado.gexf

Exemplo:

comentarios.json:
    {"de": "ana", "para": "bruno", "peso": 5}

mapeamento_vertices.json precisa conter:
    "ana": 0
    "bruno": 1

Se o mapeamento não tiver "ana" e "bruno", essa interação é ignorada.
