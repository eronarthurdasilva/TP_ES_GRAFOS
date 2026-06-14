"""
Carrega e expõe as configurações necessárias para a extração de dados
do repositório GitHub, lendo as variáveis sensíveis do arquivo .env
localizado na raiz do projeto.

Este módulo define:
- as credenciais do GitHub (token, dono e repositório);
- os caminhos de saída para os arquivos de dados brutos e processados;
- as validações que impedem a execução quando alguma configuração obrigatória
  estiver faltando.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(dotenv_path: Path) -> bool:
        if not dotenv_path.exists():
            return False

        for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

        return True

# A raiz do projeto é três níveis acima deste arquivo.
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# O .env pode estar junto deste módulo ou na raiz do projeto, dependendo de
# como o repositório foi organizado no checkout.
ENV_FILES = [
    Path(__file__).resolve().parent / ".env",
    ROOT_DIR / ".env",
]
for _env_file in ENV_FILES:
    if _env_file.exists():
        load_dotenv(_env_file)
        break

# Credenciais e identificadores do repositório que serão usados na extração.
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()

REPOSITORIOS = {
    "h3": {"owner": "h3js", "repo": "h3"},
    "hyprland": {"owner": "hyprwm", "repo": "Hyprland"},
}

# Diretório deste módulo e caminhos de saída para os dados coletados.
BASE_DIR = Path(__file__).resolve().parent
DADOS_BRUTOS = BASE_DIR / "dados_brutos"
DADOS_PROC = BASE_DIR / "dados_processados"

# Garante que os diretórios de saída existam antes de gravar arquivos.
DADOS_BRUTOS.mkdir(parents=True, exist_ok=True)
DADOS_PROC.mkdir(parents=True, exist_ok=True)

def obter_config_repositorio(repo_slug: str) -> dict:
    """Retorna owner e repo do repositório informado."""
    if repo_slug not in REPOSITORIOS:
        raise ValueError(f"Repositório desconhecido: {repo_slug}. Opções: {list(REPOSITORIOS.keys())}")

    return REPOSITORIOS[repo_slug]


def obter_diretorios_dados(repo_slug: str) -> tuple[Path, Path]:
    """Retorna os diretórios de bruto e processado para o repositório."""
    if repo_slug == "h3":
        bruto = DADOS_BRUTOS
        processado = DADOS_PROC
    else:
        bruto = DADOS_BRUTOS / repo_slug
        processado = DADOS_PROC / repo_slug

    bruto.mkdir(parents=True, exist_ok=True)
    processado.mkdir(parents=True, exist_ok=True)
    return bruto, processado


def obter_caminho_mapeamento(repo_slug: str) -> Path:
    """Retorna o arquivo de mapeamento de vértices para o repositório."""
    base_mapeamento = BASE_DIR.parent / "ConstrucaoGrafos"

    if repo_slug == "h3":
        return base_mapeamento / "mapeamento_vertices.json"

    return base_mapeamento / f"mapeamento_vertices_{repo_slug}.json"

if GITHUB_TOKEN == "your_personal_access_token":
    raise RuntimeError(
        "GITHUB_TOKEN ainda está com o valor de exemplo no .env. "
        "Substitua por um token pessoal válido do GitHub antes de executar a extração."
    )

# Exportações explícitas do módulo para facilitar imports.
__all__ = [
    "GITHUB_TOKEN",
    "REPOSITORIOS",
    "DADOS_BRUTOS",
    "DADOS_PROC",
    "obter_config_repositorio",
    "obter_diretorios_dados",
    "obter_caminho_mapeamento",
]
