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
from dotenv import load_dotenv

# A raiz do projeto é três níveis acima deste arquivo.
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Carrega as variáveis de ambiente do arquivo .env na raiz do projeto.
load_dotenv(ROOT_DIR / '.env')

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

# Exportações explícitas do módulo para facilitar imports.
__all__ = [
    "GITHUB_TOKEN",
    "GITHUB_REPO",
    "GITHUB_OWNER",
    "DADOS_BRUTOS",
    "DADOS_PROC",
]
