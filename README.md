# TP_ES_GRAFOS

Projeto de grafos para análise de colaboração em repositórios GitHub.

O fluxo principal coleta, processa e monta os grafos a partir de issues, pull requests, comentários, revisões e merges. As métricas são executadas automaticamente após a construção dos grafos, e a exportação dos grafos também roda por padrão.

Ponto de entrada atual: `Biblioteca/main.py` (execute a partir da raiz do workspace conforme os exemplos abaixo).

Repositórios disponíveis pela flag `--repo`:

- `h3` -> usa `h3js/h3`
- `hyprland` -> usa `hyprwm/Hyprland`

Uso recomendado:

```bash
cd TP_ES_GRAFOS/Biblioteca
/usr/bin/python3 main.py --repo hyprland
```

Sem exportar os grafos:

```bash
cd TP_ES_GRAFOS/Biblioteca
/usr/bin/python3 main.py --process-only --repo hyprland --sem-exportacao
```

Para o repositório `h3`, troque apenas `--repo hyprland` por `--repo h3`.

Relatório detalhado das métricas:

- `Biblioteca/Metricas/report_detalhado.py` imprime centralidade, estrutura e comunidade com nomes de usuários.
- O `main.py` chama esse relatório automaticamente ao final do processamento.

Exportação de grafos:

- `Biblioteca/ExportacaoGrafos/saida_gexf/<repo>/` gera os arquivos `.gexf`.
- `Biblioteca/ExportacaoGrafos/saida_gui/<repo>/` gera os arquivos da interface textual.
- Use `--sem-exportacao` para rodar sem exportar os grafos.

Estrutura de dados por repositório:

- `Biblioteca/ExtracaoDados/dados_brutos/` para o repositório `h3`
- `Biblioteca/ExtracaoDados/dados_brutos/hyprland/` para o repositório `hyprland`
- `Biblioteca/ExtracaoDados/dados_processados/` para o repositório `h3`
- `Biblioteca/ExtracaoDados/dados_processados/hyprland/` para o repositório `hyprland`

As saídas das métricas ficam em `Biblioteca/Metricas/saida_metricas/`, separadas por repositório.