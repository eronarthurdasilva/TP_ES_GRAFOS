#!/usr/bin/env python3
"""
Ponto de entrada para a extração de dados do repositório GitHub.
Executa a coleta de issues e pull requests.
"""

import argparse
from extracao_de_dados import ExtracaoDados

# Este arquivo é o script principal usado para iniciar o processo de
# extração de dados. Ao executá-lo, ele instancia a classe responsável
# pela coleta e dispara a extração.

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coleta e processa dados do GitHub")
    parser.add_argument(
        "--process-only",
        "-p",
        action="store_true",
        help="Não faça a coleta; apenas processe JSONs brutos existentes (se houver).",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Forçar a coleta mesmo se existirem JSONs brutos locais.",
    )
    args = parser.parse_args()

    extrator = ExtracaoDados()
    extrator.run(process_only=args.process_only, force=args.force)
