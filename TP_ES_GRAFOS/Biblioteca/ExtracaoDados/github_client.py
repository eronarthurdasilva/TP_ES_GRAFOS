"""
Cliente HTTP para comunicação com a API GraphQL do GitHub.
Encapsula autenticação, retry com backoff exponencial e tratamento de erros.
"""

import json
import time
from typing import Any, Dict, Optional

import requests


class GitHubClient:
    """Realiza requisições autenticadas à API GraphQL do GitHub."""

    MAX_TENTATIVAS = 4
    ESPERA_INICIAL = 1.0

    def __init__(self, token: str) -> None:
        self.url = "https://api.github.com/graphql"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def run_query(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Executa uma query GraphQL no GitHub com retry e backoff exponencial.

        Esta função envia a query e aguarda o resultado. Se o GitHub retornar
        um erro temporário, ela tenta novamente até um número máximo de tentativas.

        Args:
            query: Query GraphQL a ser executada.
            variables: Variáveis da query (opcional).

        Returns:
            O payload JSON retornado pela API, contendo ao menos o campo 'data'.

        Raises:
            RuntimeError: em caso de falha de rede, erro HTTP ou erro GraphQL.
        """
        espera = self.ESPERA_INICIAL

        for tentativa in range(1, self.MAX_TENTATIVAS + 1):
            try:
                response = requests.post(
                    self.url,
                    headers=self.headers,
                    json={"query": query, "variables": variables or {}},
                    timeout=30,
                )
            except requests.RequestException as exc:
                if tentativa == self.MAX_TENTATIVAS:
                    raise RuntimeError("Falha na requisição de rede ao GitHub") from exc
                time.sleep(espera)
                espera *= 2
                continue

            try:
                payload = response.json()
            except ValueError:
                if response.status_code >= 500 and tentativa < self.MAX_TENTATIVAS:
                    time.sleep(espera)
                    espera *= 2
                    continue
                raise RuntimeError(
                    f"Resposta inválida do GitHub: status={response.status_code}, corpo={response.text}"
                )

            if response.status_code >= 500 and tentativa < self.MAX_TENTATIVAS:
                time.sleep(espera)
                espera *= 2
                continue

            if response.status_code != 200:
                raise RuntimeError(
                    f"Erro GitHub GraphQL: status={response.status_code}, "
                    f"corpo={json.dumps(payload, ensure_ascii=False)}"
                )

            if "errors" in payload:
                raise RuntimeError(
                    f"Erros GraphQL: {json.dumps(payload['errors'], ensure_ascii=False)}"
                )

            if "data" not in payload:
                raise RuntimeError(
                    f"Resposta inesperada: campo 'data' ausente, "
                    f"payload={json.dumps(payload, ensure_ascii=False)}"
                )

            return payload

        raise RuntimeError("Falhou após todas as tentativas")