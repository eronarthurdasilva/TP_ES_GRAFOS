"""Ferramentas para mapear usuários a índices inteiros do grafo.

O objetivo deste módulo é percorrer uma vez os JSONs já processados em
dados_processados/ e gerar dois níveis de informação:

1. Um mapa global estável no formato:

	{
		"vaxerski": 0,
		"palontologist": 1,
		"Euro20179": 2,
		...
	}

2. Uma separação por arquivo processado, para identificar quais usuários
aparecem em comentarios.json, fechamentos.json e reviews_merges.json.

O mapa global continua sendo útil para o grafo, enquanto a separação por
arquivo facilita a análise da origem dos vértices.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set


class MapeamentoVertices:
	"""Gera e persiste o mapa de usuários para índices inteiros."""

	def __init__(self, dados_processados: Path) -> None:
		self.dados_processados = Path(dados_processados)

	def gerar(self) -> Dict[str, int]:
		"""Lê os JSONs processados uma única vez e retorna o mapa nome -> índice."""
		usuarios = self._coletar_usuarios_unicos()
		return {usuario: indice for indice, usuario in enumerate(usuarios)}

	def gerar_por_arquivo(self) -> Dict[str, Any]:
		"""Retorna os usuários separados por arquivo e também o mapa global."""
		por_arquivo: Dict[str, Any] = {}
		usuarios_globais: Set[str] = set()

		for arquivo_json in self._arquivos_processados():
			usuarios_arquivo = self._coletar_usuarios_do_arquivo(arquivo_json)
			usuarios_globais.update(usuarios_arquivo)
			por_arquivo[arquivo_json.name] = {
				"usuarios": usuarios_arquivo,
				"mapeamento": {
					usuario: indice for indice, usuario in enumerate(usuarios_arquivo)
				},
			}

		usuarios_globais_ordenados = sorted(usuarios_globais)
		return {
			"arquivos": por_arquivo,
			"global": {
				"usuarios": usuarios_globais_ordenados,
				"mapeamento": {
					usuario: indice for indice, usuario in enumerate(usuarios_globais_ordenados)
				},
			},
		}

	def salvar(self, arquivo_saida: Path) -> Dict[str, int]:
		"""Gera o mapa global e o salva em JSON no caminho informado."""
		mapeamento = self.gerar_por_arquivo()
		arquivo_saida = Path(arquivo_saida)
		arquivo_saida.parent.mkdir(parents=True, exist_ok=True)

		with arquivo_saida.open("w", encoding="utf-8") as arquivo:
			json.dump(mapeamento, arquivo, ensure_ascii=False, indent=2)

		return mapeamento

	def _coletar_usuarios_unicos(self) -> List[str]:
		"""Coleta os logins únicos presentes em 'de' e 'para' em todos os JSONs."""
		usuarios: Set[str] = set()

		for arquivo_json in self._arquivos_processados():
			for item in self._carregar_itens(arquivo_json):
				for campo in ("de", "para"):
					valor = item.get(campo)
					if isinstance(valor, str) and valor.strip():
						usuarios.add(valor.strip())

		return sorted(usuarios)

	def _coletar_usuarios_do_arquivo(self, arquivo_json: Path) -> List[str]:
		"""Coleta os logins únicos presentes em 'de' e 'para' de um arquivo."""
		usuarios: Set[str] = set()

		for item in self._carregar_itens(arquivo_json):
			for campo in ("de", "para"):
				valor = item.get(campo)
				if isinstance(valor, str) and valor.strip():
					usuarios.add(valor.strip())

		return sorted(usuarios)

	def _arquivos_processados(self) -> List[Path]:
		"""Retorna os arquivos processados que devem entrar no mapa."""
		nomes = [
			"comentarios.json",
			"fechamentos.json",
			"reviews_merges.json",
		]
		return [self.dados_processados / nome for nome in nomes if (self.dados_processados / nome).exists()]

	def _carregar_itens(self, arquivo_json: Path) -> List[dict]:
		"""Lê um arquivo JSON e normaliza o conteúdo para uma lista de dicionários."""
		with arquivo_json.open("r", encoding="utf-8") as arquivo:
			dados = json.load(arquivo)

		if isinstance(dados, list):
			return [item for item in dados if isinstance(item, dict)]

		if isinstance(dados, dict):
			if "nodes" in dados and isinstance(dados["nodes"], list):
				return [item for item in dados["nodes"] if isinstance(item, dict)]
			if "items" in dados and isinstance(dados["items"], list):
				return [item for item in dados["items"] if isinstance(item, dict)]
			return [dados]

		return []


def gerar_mapeamento_vertices(dados_processados: Path, arquivo_saida: Path | None = None) -> Dict[str, Any]:
	"""Atalho funcional para gerar o mapa de usuários."""
	mapeador = MapeamentoVertices(dados_processados)

	if arquivo_saida is not None:
		return mapeador.salvar(arquivo_saida)

	return mapeador.gerar()


if __name__ == "__main__":
	base_dir = Path(__file__).resolve().parent.parent / "ExtracaoDados" / "dados_processados"
	saida_padrao = Path(__file__).resolve().parent / "mapeamento_vertices.json"
	mapeamento = gerar_mapeamento_vertices(base_dir, saida_padrao)
	print(f"Mapeamento gerado com {len(mapeamento)} vertices em {saida_padrao}")
