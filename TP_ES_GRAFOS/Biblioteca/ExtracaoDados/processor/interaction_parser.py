"""
Responsabilidade: ler os JSONs brutos de dados_brutos/ e separar
as interações entre usuários em 3 arquivos em dados_processados/:

    comentarios.json     → comentários em issues e PRs         (peso 2)
    fechamentos.json     → fechamento de issue por outro usuário (peso 3)
    reviews_merges.json  → revisões, aprovações e merges de PRs (peso 4 ou 5)

Cada interação é salva no formato:
    {
        "de":   "login_de_quem_agiu",
        "para": "login_de_quem_recebeu",
        "tipo": "comentario_issue" | "comentario_pr" | "fechamento" | "aprovacao" | "merge",
        "peso": 2 | 3 | 4 | 5
    }

Interações onde "de" == "para" são ignoradas (usuário interagindo consigo mesmo).
Interações com autor None/null (bots deletados ou usuários anônimos) são ignoradas.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


# ─── Pesos conforme o enunciado ───────────────────────────────────────────────
PESO_COMENTARIO = 2   # comentário em issue ou PR
PESO_FECHAMENTO = 3   # abertura de issue comentada/fechada por outro usuário
PESO_APROVACAO  = 4   # revisão/aprovação de PR
PESO_MERGE      = 5   # merge de PR


class InteractionParser:
    """Transforma JSONs brutos em interações tipadas prontas para o grafo."""

    def __init__(self, dados_brutos: Path, dados_processados: Path) -> None:
        self.dados_brutos      = Path(dados_brutos)
        self.dados_processados = Path(dados_processados)

        # Garante que o diretório de saída existe
        self.dados_processados.mkdir(parents=True, exist_ok=True)

    # ─── API pública ──────────────────────────────────────────────────────────

    def parse(self) -> None:
        """Ponto de entrada: processa issues e PRs e salva os 3 arquivos."""
        print("Iniciando processamento das interações...")

        comentarios    = self._processar_issues() + self._processar_comentarios_pr()
        fechamentos    = self._processar_fechamentos()
        reviews_merges = self._processar_reviews_merges()

        self._salvar("comentarios.json",    comentarios)
        self._salvar("fechamentos.json",    fechamentos)
        self._salvar("reviews_merges.json", reviews_merges)

        print(
            f"Processamento finalizado.\n"
            f"  comentarios:    {len(comentarios)}\n"
            f"  fechamentos:    {len(fechamentos)}\n"
            f"  reviews/merges: {len(reviews_merges)}"
        )

    # ─── Processadores internos ───────────────────────────────────────────────

    def _processar_issues(self) -> List[Dict[str, Any]]:
        """
        Extrai comentários feitos em issues.
        Regra: quem comentou → quem abriu a issue (peso 2).
        """
        interacoes = []

        for issue in self._carregar_chunks("issues"):
            autor_issue = self._login(issue.get("author"))
            if not autor_issue:
                # Issue sem autor identificável (ex: usuário deletado) — ignora
                continue

            for comentario in issue.get("comments", {}).get("nodes", []):
                autor_comentario = self._login(comentario.get("author"))
                if not autor_comentario:
                    continue

                # Ignora auto-comentário (usuário comentando na própria issue)
                if autor_comentario == autor_issue:
                    continue

                interacoes.append({
                    "de":   autor_comentario,
                    "para": autor_issue,
                    "tipo": "comentario_issue",
                    "peso": PESO_COMENTARIO,
                })

        return interacoes

    def _processar_fechamentos(self) -> List[Dict[str, Any]]:
        """
        Extrai fechamentos de issues feitos por outro usuário.
        Regra: quem fechou → quem abriu (peso 3).

        O campo closer pode ser:
            - PullRequest → quem fez merge fechou a issue
            - Commit      → quem fez o commit fechou a issue
            - None        → fechamento manual sem vínculo (ignorado)
        """
        interacoes = []

        for issue in self._carregar_chunks("issues"):
            if issue.get("state") != "CLOSED":
                continue

            autor_issue = self._login(issue.get("author"))
            if not autor_issue:
                continue

            # Navega até o ClosedEvent dentro de timelineItems
            timeline_nodes = (
                issue.get("timelineItems", {}).get("nodes", [])
            )
            if not timeline_nodes:
                continue

            closed_event = timeline_nodes[0]            # last: 1 → só 1 nó
            closer       = closed_event.get("closer")
            if not closer:
                continue

            typename = closer.get("__typename")
            quem_fechou: Optional[str] = None

            if typename == "PullRequest":
                # PR que fechou a issue — quem fez merge é o responsável
                quem_fechou = self._login(closer.get("mergedBy"))

            elif typename == "Commit":
                # Commit direto — tenta pegar o usuário GitHub vinculado ao commit
                commit_author = closer.get("author", {})
                quem_fechou   = self._login(commit_author.get("user")) or commit_author.get("name")

            if not quem_fechou or quem_fechou == autor_issue:
                continue

            interacoes.append({
                "de":   quem_fechou,
                "para": autor_issue,
                "tipo": "fechamento",
                "peso": PESO_FECHAMENTO,
            })

        return interacoes

    def _processar_comentarios_pr(self) -> List[Dict[str, Any]]:
        """
        Extrai comentários feitos em pull requests.
        Regra: quem comentou → quem abriu o PR (peso 2).
        """
        interacoes = []

        for pr in self._carregar_chunks("pull_requests"):
            autor_pr = self._login(pr.get("author"))
            if not autor_pr:
                continue

            for comentario in pr.get("comments", {}).get("nodes", []):
                autor_comentario = self._login(comentario.get("author"))
                if not autor_comentario or autor_comentario == autor_pr:
                    continue

                interacoes.append({
                    "de":   autor_comentario,
                    "para": autor_pr,
                    "tipo": "comentario_pr",
                    "peso": PESO_COMENTARIO,
                })

        return interacoes

    def _processar_reviews_merges(self) -> List[Dict[str, Any]]:
        """
        Extrai revisões/aprovações e merges de pull requests.

        Regras:
            - Review com state APPROVED ou CHANGES_REQUESTED → peso 4
              (ambos representam análise técnica relevante)
            - Merge → peso 5
        """
        interacoes = []

        for pr in self._carregar_chunks("pull_requests"):
            autor_pr = self._login(pr.get("author"))
            if not autor_pr:
                continue

            # Reviews (aprovações e pedidos de mudança)
            for review in pr.get("reviews", {}).get("nodes", []):
                autor_review = self._login(review.get("author"))
                estado       = review.get("state", "")

                if not autor_review or autor_review == autor_pr:
                    continue

                # Só conta reviews que representam análise técnica real
                if estado not in ("APPROVED", "CHANGES_REQUESTED"):
                    continue

                tipo = "aprovacao" if estado == "APPROVED" else "revisao"

                interacoes.append({
                    "de":   autor_review,
                    "para": autor_pr,
                    "tipo": tipo,
                    "peso": PESO_APROVACAO,
                })

            # Merge
            quem_mergeu = self._login(pr.get("mergedBy"))
            if quem_mergeu and quem_mergeu != autor_pr:
                interacoes.append({
                    "de":   quem_mergeu,
                    "para": autor_pr,
                    "tipo": "merge",
                    "peso": PESO_MERGE,
                })

        return interacoes

    # ─── Utilitários ──────────────────────────────────────────────────────────

    def _carregar_chunks(self, prefixo: str) -> List[Dict[str, Any]]:
        """
        Lê todos os arquivos <prefixo>_*.json de dados_brutos/
        e retorna uma lista única com todos os itens.

        Exemplo: prefixo="issues" lê issues_1.json, issues_2.json, ...
        """
        todos = []
        arquivos = sorted(self.dados_brutos.glob(f"{prefixo}_*.json"))

        if not arquivos:
            print(f"Aviso: nenhum arquivo {prefixo}_*.json encontrado em {self.dados_brutos}")
            return todos

        for arquivo in arquivos:
            with arquivo.open("r", encoding="utf-8") as f:
                dados = json.load(f)
                todos.extend(dados)

        return todos

    def _salvar(self, nome_arquivo: str, dados: List[Dict[str, Any]]) -> None:
        """Salva uma lista de interações em dados_processados/<nome_arquivo>."""
        caminho = self.dados_processados / nome_arquivo
        with caminho.open("w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        print(f"Salvo {len(dados):>6} interações → {nome_arquivo}")

    @staticmethod
    def _login(obj: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Extrai o login de um objeto autor do GraphQL.
        Retorna None se o objeto for None ou não tiver 'login'.

        Exemplos de entrada:
            {"login": "vaxry"}  → "vaxry"
            None                → None
            {}                  → None
        """
        if not obj:
            return None
        return obj.get("login") or None