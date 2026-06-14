# TP_ES_GRAFOS

Projeto de grafos para análise de colaboração em repositórios GitHub.

O fluxo principal coleta, processa e monta os grafos a partir de issues, pull requests, comentários, revisões e merges. As métricas são executadas automaticamente após a construção dos grafos.

Ponto de entrada atual: `Biblioteca/main.py` (execute a partir da raiz do workspace conforme os exemplos abaixo).

Repositórios disponíveis pela flag `--repo`:

- `h3` -> usa `h3js/h3`
- `hyprland` -> usa `hyprwm/Hyprland`

Comandos úteis:

```bash
cd TP_ES_GRAFOS/Biblioteca
/usr/bin/python3 main.py --repo h3
```

```bash
cd TP_ES_GRAFOS/Biblioteca
/usr/bin/python3 main.py --repo hyprland
```

```bash
cd TP_ES_GRAFOS/Biblioteca
/usr/bin/python3 main.py --process-only --repo hyprland
```

Estrutura de dados por repositório:

- `Biblioteca/ExtracaoDados/dados_brutos/` para o repositório `h3`
- `Biblioteca/ExtracaoDados/dados_brutos/hyprland/` para o repositório `hyprland`
- `Biblioteca/ExtracaoDados/dados_processados/` para o repositório `h3`
- `Biblioteca/ExtracaoDados/dados_processados/hyprland/` para o repositório `hyprland`

As saídas das métricas ficam em `Biblioteca/Metricas/saida_metricas/`, separadas por repositório.