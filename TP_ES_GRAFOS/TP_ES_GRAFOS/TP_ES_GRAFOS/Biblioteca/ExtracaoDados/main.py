#!/usr/bin/env python3
"""
Ponto de entrada para a extração de dados do repositório GitHub.
Executa a coleta de issues e pull requests.
"""

from extracao_de_dados import ExtracaoDados

# Este arquivo é o script principal usado para iniciar o processo de
# extração de dados. Ao executá-lo, ele instancia a classe responsável
# pela coleta e dispara a extração.

if __name__ == "__main__":
    extrator = ExtracaoDados()
    extrator.run()
