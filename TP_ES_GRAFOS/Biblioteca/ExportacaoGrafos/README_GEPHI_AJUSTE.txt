AJUSTE PARA VISUALIZAÇÃO NO GEPHI

O problema de aparecer uma grande mancha/polígono cinza no Gephi normalmente
acontece por dois motivos:

1) Os pesos reais das arestas são muito altos.
   O Gephi usa o campo weight para desenhar/interpretar as arestas. Quando o
   peso é grande demais, algumas arestas ficam grossas a ponto de parecerem
   polígonos.

2) O arquivo exportava muitos vértices isolados.
   Isso cria uma massa de pontos sem conexão, dificultando a visualização.

O que esta versão faz:

- Exporta, por padrão, apenas vértices que possuem pelo menos uma aresta.
- Ignora auto-laços por padrão, ou seja, arestas do tipo usuário -> mesmo usuário.
- Normaliza o peso visual das arestas para a faixa 1.0 até 5.0.
- Preserva o peso real no atributo peso_original.

Como rodar:

A partir da pasta raiz do projeto:

    python ExportacaoGrafos/RodarExportacao.py

Ou, no Windows:

    py ExportacaoGrafos/RodarExportacao.py

Depois abra no Gephi:

    ExportacaoGrafos/saida_gexf/grafo_4_integrado.gexf

No Gephi, faça:

1. Abra o arquivo .gexf.
2. Vá para Overview.
3. Em Layout, escolha ForceAtlas 2 ou Fruchterman Reingold.
4. Clique em Run por alguns segundos e depois Stop.
5. Se ainda estiver muito carregado, em Appearance reduza a espessura das arestas.

Comandos opcionais:

Exportar também vértices isolados:

    python ExportacaoGrafos/ExportacaoGexf.py --com-isolados

Manter auto-laços:

    python ExportacaoGrafos/ExportacaoGexf.py --manter-auto-lacos

Usar pesos reais diretamente no campo weight:

    python ExportacaoGrafos/ExportacaoGexf.py --sem-normalizar-pesos

OBS: usar pesos reais pode fazer o Gephi voltar a mostrar arestas gigantes.
