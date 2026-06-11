import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class PRFetcher:
    """Coleta pull requests do GitHub e grava os resultados em arquivos JSON."""

    def __init__(self, client: Any, owner: str, repo: str, output_dir: str) -> None:
        self.client = client
        self.owner = owner
        self.repo = repo
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Query GraphQL para buscar pull requests e dados de revisão/comentários.
        self.query = """
        query PRFetcherQuery($owner: String!, $repo: String!, $cursor: String) {
          repository(owner: $owner, name: $repo) {
            pullRequests(first: 100, after: $cursor, orderBy: {field: CREATED_AT, direction: ASC}) {
              nodes {
                number
                title
                state
                createdAt
                mergedAt
                author {
                  login
                }
                mergedBy {
                  login
                }
                reviews(first: 100) {
                  nodes {
                    author {
                      login
                    }
                    state
                  }
                }
                comments(first: 100) {
                  nodes {
                    author {
                      login
                    }
                    createdAt
                  }
                }
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
        """

    def _salvar_chunk(self, dados: List[Dict[str, Any]], indice: int) -> None:
        caminho = self.output_dir / f"pull_requests_{indice}.json"
        with caminho.open("w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, indent=2, ensure_ascii=False)

        print(f"Salvo {len(dados)} pull requests -> {caminho.name}")

    def fetch(self) -> None:
        """Busca todas as pull requests paginadas e salva em arquivos de até 500 itens."""
        cursor: Optional[str] = None
        buffer: List[Dict[str, Any]] = []
        chunk = 1

        print("Iniciando coleta de pull requests...")

        while True:
            resultado = self.client.run_query(
                self.query,
                {
                    "owner": self.owner,
                    "repo": self.repo,
                    "cursor": cursor,
                },
            )

            prs = resultado["data"]["repository"]["pullRequests"]
            nodes = prs["nodes"]
            buffer.extend(nodes)

            print(f"Coletadas {len(nodes)} pull requests (total no buffer: {len(buffer)})")

            if len(buffer) >= 500:
                self._salvar_chunk(buffer[:500], chunk)
                buffer = buffer[500:]
                chunk += 1

            if not prs["pageInfo"]["hasNextPage"]:
                break

            cursor = prs["pageInfo"]["endCursor"]
            time.sleep(0.5)

        if buffer:
            self._salvar_chunk(buffer, chunk)

        print("Coleta de pull requests finalizada.")
