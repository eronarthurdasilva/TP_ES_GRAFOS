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
GITHUB_REPO = os.getenv("GITHUB_REPO", "").strip()
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "").strip()

# Diretório deste módulo e caminhos de saída para os dados coletados.
BASE_DIR = Path(__file__).resolve().parent
DADOS_BRUTOS = BASE_DIR / "dados_brutos"
DADOS_PROC = BASE_DIR / "dados_processados"

# Garante que os diretórios de saída existam antes de gravar arquivos.
DADOS_BRUTOS.mkdir(parents=True, exist_ok=True)
DADOS_PROC.mkdir(parents=True, exist_ok=True)

# Verifica rapidamente se todas as variáveis obrigatórias foram carregadas.
_obrigatorias = {
    "GITHUB_TOKEN": GITHUB_TOKEN,
    "GITHUB_OWNER": GITHUB_OWNER,
    "GITHUB_REPO": GITHUB_REPO,
}
for _nome, _valor in _obrigatorias.items():
    if not _valor:
        raise RuntimeError(f"{_nome} não encontrado ou vazio no .env")

if GITHUB_TOKEN == "your_personal_access_token":
    raise RuntimeError(
        "GITHUB_TOKEN ainda está com o valor de exemplo no .env. "
        "Substitua por um token pessoal válido do GitHub antes de executar a extração."
    )

# Exportações explícitas do módulo para facilitar imports.
__all__ = [
    "GITHUB_TOKEN",
    "GITHUB_REPO",
    "GITHUB_OWNER",
    "DADOS_BRUTOS",
    "DADOS_PROC",
]
