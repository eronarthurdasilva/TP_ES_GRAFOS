"""RodarExemploLocal.py
======================

Roda uma exportação pequena, mas com arestas reais.

Use este arquivo apenas para testar se o exportador está funcionando:

    python RodarExemploLocal.py

Ele usa:
    dados_exemplo_processados/
    mapeamento_vertices_exemplo.json

E gera:
    saida_gexf_exemplo/
"""

from pathlib import Path
from ExportacaoGexf import ExportacaoGexf


PASTA_ATUAL = Path(__file__).resolve().parent

exportador = ExportacaoGexf(
    dados_processados=PASTA_ATUAL / "dados_exemplo_processados",
    arquivo_mapeamento=PASTA_ATUAL / "mapeamento_vertices_exemplo.json",
    pasta_saida=PASTA_ATUAL / "saida_gexf_exemplo",
    # No exemplo, deixei False para aparecerem apenas vértices conectados.
    # Assim fica mais fácil ver as arestas no Gephi.
    exportar_vertices_isolados=False,
)

exportador.exportar_todos()

print("Exemplo finalizado.")
print("Arquivos gerados em: saida_gexf_exemplo")
print("Abra no Gephi, por exemplo: saida_gexf_exemplo/grafo_4_integrado.gexf")
