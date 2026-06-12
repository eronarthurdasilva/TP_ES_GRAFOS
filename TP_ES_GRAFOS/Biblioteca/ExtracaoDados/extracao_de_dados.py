from config import (
    DADOS_BRUTOS,
    DADOS_PROC,
    GITHUB_OWNER,
    GITHUB_REPO,
    GITHUB_TOKEN,
)
from github_client import GitHubClient
from issues_fetcher import IssuesFetcher
from pr_fetcher import PRFetcher
from processor.interaction_parser import InteractionParser


class ExtracaoDados:
    """Organiza a extração de dados do GitHub em etapas claras.

    Esta classe monta os coletores necessários e coordena a execução da
    extração de issues e pull requests do repositório configurado.
    """

    def __init__(self) -> None:
        # Cria o cliente GitHub com o token de autenticação.
        client = GitHubClient(GITHUB_TOKEN)

        # Inicializa o coletor de issues e passa o diretório onde os arquivos
        # brutos serão gravados.
        self.issues_fetcher = IssuesFetcher(
            client,
            GITHUB_OWNER,
            GITHUB_REPO,
            DADOS_BRUTOS,
        )

        # Inicializa o coletor de pull requests com as mesmas configurações.
        self.pr_fetcher = PRFetcher(
            client,
            GITHUB_OWNER,
            GITHUB_REPO,
            DADOS_BRUTOS,
        )

        # Processa os JSONs brutos gerados pela coleta em arquivos prontos
        # para a construção do grafo.
        self.interaction_parser = InteractionParser(DADOS_BRUTOS, DADOS_PROC)

    def _tem_dados_brutos(self) -> bool:
        # Detecta arquivos com os prefixos esperados para evitar falsos positivos
        patterns = ["issues_*.json", "pull_requests_*.json", "*.json"]
        found = []
        for p in patterns:
            for f in DADOS_BRUTOS.glob(p):
                found.append(f.name)
        return len(found) > 0

    def _listar_dados_brutos(self) -> list:
        patterns = ["issues_*.json", "pull_requests_*.json", "*.json"]
        found = []
        for p in patterns:
            for f in DADOS_BRUTOS.glob(p):
                found.append(f.name)
        return sorted(set(found))

    def run(self, process_only: bool = False, force: bool = False) -> None:
        if process_only:
            if not self._tem_dados_brutos():
                print(
                    "Modo process_only solicitado, mas não há JSONs brutos em "
                    f"{DADOS_BRUTOS}. Execute a coleta primeiro."
                )
                return
            arquivos = self._listar_dados_brutos()
            print("Modo process_only ativo: pulando coleta e processando JSONs existentes...")
            print(f"Arquivos encontrados em {DADOS_BRUTOS}: {arquivos}")
            self.interaction_parser.parse()
            print("Processamento completo.")
            return

        # Novo comportamento: se já houver dados brutos e não houver --force,
        # não execute a coleta e processe apenas os arquivos existentes.
        if self._tem_dados_brutos() and not force:
            arquivos = self._listar_dados_brutos()
            print(
                "Dados brutos detectados: pulando coleta automática."
                f" Use --force para forçar nova coleta. Arquivos: {arquivos}"
            )
            self.interaction_parser.parse()
            print("Processamento completo.")
            return

        # Comportamento padrão: realizar a coleta e depois processar.
        self.issues_fetcher.fetch()
        self.pr_fetcher.fetch()
        self.interaction_parser.parse()
        print("Extração completa.")