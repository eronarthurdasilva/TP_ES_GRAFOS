from config import GITHUB_OWNER, GITHUB_REPO, GITHUB_TOKEN, DADOS_BRUTOS
from github_client import GitHubClient
from issues_fetcher import IssuesFetcher
from pr_fetcher import PRFetcher


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

    def run(self) -> None:
        self.issues_fetcher.fetch()
        self.pr_fetcher.fetch()
        print("Extração completa.")