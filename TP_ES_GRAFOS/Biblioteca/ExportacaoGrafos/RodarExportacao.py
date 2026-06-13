"""RodarExportacao.py
====================

Arquivo principal para rodar a exportacao dos 4 grafos reais do trabalho.

Como usar, a partir da pasta raiz do projeto:
    python ExportacaoGrafos/RodarExportacao.py

ou, no Windows:
    py ExportacaoGrafos/RodarExportacao.py

Estrutura esperada:
    Projeto/
    ├── ConstrucaoGrafos/
    │   └── mapeamento_vertices.json
    ├── ExtracaoDados/
    │   └── dados_processados/
    │       ├── comentarios.json
    │       ├── fechamentos.json
    │       └── reviews_merges.json
    └── ExportacaoGrafos/
        ├── ExportacaoGexf.py
        └── RodarExportacao.py
"""

from ExportacaoGexf import ExportacaoGexf


exportador = ExportacaoGexf(
    # None usa o caminho padrao:
    # ../ExtracaoDados/dados_processados
    dados_processados=None,

    # None tenta encontrar automaticamente:
    # ../ConstrucaoGrafos/mapeamento_vertices.json
    # ou ./mapeamento_vertices.json
    arquivo_mapeamento=None,

    # None gera os arquivos em:
    # ./saida_gexf
    pasta_saida=None,

    # False: exporta somente vértices que possuem arestas.
    # Isso evita milhares de pontos isolados no Gephi.
    exportar_vertices_isolados=False,

    # True: remove auto-laços, ou seja, arestas do tipo usuario -> ele mesmo.
    # Isso costuma melhorar bastante a visualização no Gephi.
    ignorar_auto_lacos=True,

    # True: coloca no campo weight um peso menor, próprio para visualização.
    # O peso real fica preservado no atributo peso_original.
    normalizar_pesos_gephi=True,

    # Faixa do peso visual das arestas no Gephi.
    peso_visual_minimo=1.0,
    peso_visual_maximo=5.0,
)

exportador.exportar_todos()

print("Exportacao finalizada.")
print("Arquivos gerados na pasta: saida_gexf")
