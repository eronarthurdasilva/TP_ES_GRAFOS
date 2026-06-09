import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class IssuesFetcher:
    """Coleta issues do GitHub e grava os resultados em arquivos JSON."""

    def __init__(self, client: Any, owner: str, repo: str, output_dir: str) -> None:
        self.client = client
        self.owner = owner
        self.repo = repo
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Query GraphQL para buscar issues e alguns detalhes adicionais.
        self.query = """
        query IssuesFetcherQuery($owner: String!, $repo: String!, $cursor: String) {
        repository(owner: $owner, name: $repo) {
            issues(
            first: 50
            after: $cursor
            orderBy: { field: CREATED_AT, direction: ASC }
            ) {
            nodes {
                number
                title
                state
                createdAt
                closedAt
                author { login }

                comments(first: 100) {
                nodes {
                    author { login }
                    createdAt
                }
                }

                timelineItems(last: 1, itemTypes: [CLOSED_EVENT]) {
                nodes {
                    ... on ClosedEvent {
                    closer {
                        __typename
                        ... on PullRequest {
                        number
                        mergedBy { login }
                        }
                        ... on Commit {
                        author {
                            user { login }
                            name
                        }
                        }
                    }
                    }
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
        caminho = self.output_dir / f"issues_{indice}.json"
        with caminho.open("w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, indent=2, ensure_ascii=False)

        print(f"Salvo {len(dados)} issues → {caminho.name}")

    def fetch(self) -> None:
        """Busca todas as issues paginadas e salva em arquivos de até 500 itens."""
        cursor: Optional[str] = None
        buffer: List[Dict[str, Any]] = []
        chunk = 1

        print("Iniciando coleta de issues...")

        while True:
            resultado = self.client.run_query(
                self.query,
                {
                    "owner": self.owner,
                    "repo": self.repo,
                    "cursor": cursor,
                },
            )

            issues = resultado["data"]["repository"]["issues"]
            nodes = issues["nodes"]
            buffer.extend(nodes)

            print(f"Coletadas {len(nodes)} issues (total no buffer: {len(buffer)})")

            # Quando o buffer atinge 500 itens, grava um arquivo e limpa o buffer.
            if len(buffer) >= 500:
                self._salvar_chunk(buffer[:500], chunk)
                buffer = buffer[500:]
                chunk += 1

            if not issues["pageInfo"]["hasNextPage"]:
                break

            cursor = issues["pageInfo"]["endCursor"]
            time.sleep(0.5)

        if buffer:
            self._salvar_chunk(buffer, chunk)

        print("Coleta de issues finalizada.")
