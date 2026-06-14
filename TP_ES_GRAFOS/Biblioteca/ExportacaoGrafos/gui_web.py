#!/usr/bin/env python3
"""Interface web local para visualizar metricas e acionar o pipeline."""

from __future__ import annotations

import argparse
import json
import queue
import subprocess
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from gui_backend import carregar_grafos_processados, executar_backend

BASE_DIR = Path(__file__).resolve().parent.parent
MAIN_SCRIPT = BASE_DIR / "main.py"
REPOSITORIOS = ("h3", "hyprland")
GRAFOS_CHAVES = ("comentarios", "fechamentos", "reviews_merges", "integrado")

PIPELINE = {
    "running": False,
    "returncode": None,
    "started_at": None,
    "finished_at": None,
    "command": [],
    "logs": [],
}
PIPELINE_LOCK = threading.Lock()


def debug_log(mensagem: str):
    agora = time.strftime("%H:%M:%S")
    print(f"[gui_web {agora}] {mensagem}", flush=True)


def dados_processados_repo(repo_slug: str) -> Path:
    base = BASE_DIR / "ExtracaoDados" / "dados_processados"
    if repo_slug == "h3":
        return base
    return base / repo_slug


def saida_gui_repo(repo_slug: str) -> Path:
    base = BASE_DIR / "ExportacaoGrafos" / "saida_gui"
    if repo_slug == "h3":
        return base
    return base / repo_slug


def validar_repo(repo_slug: str) -> str:
    if repo_slug not in REPOSITORIOS:
        raise ValueError(f"Repositorio invalido: {repo_slug}")
    return repo_slug


def preparar_resultado(repo_slug: str) -> dict:
    repo_slug = validar_repo(repo_slug)
    debug_log(f"Carregando resultado repo={repo_slug}")
    resultado = executar_backend(
        pasta_dados_processados=dados_processados_repo(repo_slug),
        pasta_saida=saida_gui_repo(repo_slug),
        repo_slug=repo_slug,
    )
    return resultado


def preparar_grafo(repo_slug: str, chave_grafo: str, limite_vertices: int = 80) -> dict:
    repo_slug = validar_repo(repo_slug)
    if chave_grafo not in GRAFOS_CHAVES:
        raise ValueError(f"Grafo invalido: {chave_grafo}")

    grafos = carregar_grafos_processados(dados_processados_repo(repo_slug))
    grafo = grafos[chave_grafo]

    pesos = {vertice: 0.0 for vertice in grafo["vertices"]}
    graus = {
        vertice: len(grafo["adjacencia_nao_direcionada"].get(vertice, set()))
        for vertice in grafo["vertices"]
    }

    for origem, destino in grafo["arestas_nao_direcionadas"]:
        peso = grafo["arestas_nao_direcionadas"][(origem, destino)]
        pesos[origem] = pesos.get(origem, 0.0) + peso
        pesos[destino] = pesos.get(destino, 0.0) + peso

    vertices = sorted(
        grafo["vertices"],
        key=lambda item: (pesos.get(item, 0.0), graus.get(item, 0), str(item)),
        reverse=True,
    )[:limite_vertices]
    selecionados = set(vertices)

    nodes = [
        {
            "id": str(vertice),
            "label": str(vertice),
            "weight": pesos.get(vertice, 0.0),
            "degree": graus.get(vertice, 0),
        }
        for vertice in vertices
    ]

    links = []
    for origem, destino in grafo["arestas_nao_direcionadas"]:
        if origem in selecionados and destino in selecionados:
            links.append(
                {
                    "source": str(origem),
                    "target": str(destino),
                    "weight": grafo["arestas_nao_direcionadas"][(origem, destino)],
                }
            )

    return {
        "repo": repo_slug,
        "grafo": chave_grafo,
        "nome": grafo["nome_grafo"],
        "nodes": nodes,
        "links": links,
    }


def iniciar_pipeline(repo_slug: str, process_only: bool, force: bool) -> dict:
    repo_slug = validar_repo(repo_slug)
    cmd = [sys.executable, str(MAIN_SCRIPT), "--repo", repo_slug]
    if process_only:
        cmd.append("--process-only")
    if force:
        cmd.append("--force")
    cmd.append("--sem-gui")

    with PIPELINE_LOCK:
        if PIPELINE["running"]:
            return {"started": False, "message": "Pipeline ja esta em execucao."}

        PIPELINE.update(
            {
                "running": True,
                "returncode": None,
                "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "finished_at": None,
                "command": cmd,
                "logs": [f"$ {' '.join(cmd)}\n"],
            }
        )

    debug_log(f"Iniciando pipeline: {' '.join(cmd)}")
    thread = threading.Thread(target=executar_pipeline_worker, args=(cmd,), daemon=True)
    thread.start()
    return {"started": True, "message": "Pipeline iniciado.", "command": cmd}


def executar_pipeline_worker(cmd: list[str]):
    try:
        processo = subprocess.Popen(
            cmd,
            cwd=str(BASE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert processo.stdout is not None
        for linha in processo.stdout:
            with PIPELINE_LOCK:
                PIPELINE["logs"].append(linha)

        code = processo.wait()
        debug_log(f"Pipeline finalizado code={code}")
        with PIPELINE_LOCK:
            PIPELINE["running"] = False
            PIPELINE["returncode"] = code
            PIPELINE["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            PIPELINE["logs"].append(f"\nPipeline finalizado com codigo {code}.\n")
    except Exception:
        erro = traceback.format_exc()
        debug_log("Erro no pipeline")
        print(erro, flush=True)
        with PIPELINE_LOCK:
            PIPELINE["running"] = False
            PIPELINE["returncode"] = -1
            PIPELINE["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            PIPELINE["logs"].append("\n" + erro + "\n")


def status_pipeline() -> dict:
    with PIPELINE_LOCK:
        return {
            "running": PIPELINE["running"],
            "returncode": PIPELINE["returncode"],
            "started_at": PIPELINE["started_at"],
            "finished_at": PIPELINE["finished_at"],
            "command": PIPELINE["command"],
            "logs": "".join(PIPELINE["logs"][-1200:]),
        }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, formato, *args):
        debug_log("%s - %s" % (self.address_string(), formato % args))

    def send_json(self, payload: dict, status: int = 200):
        corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def send_html(self):
        corpo = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        try:
            if parsed.path == "/":
                self.send_html()
            elif parsed.path == "/api/resultados":
                repo = params.get("repo", ["h3"])[0]
                self.send_json(preparar_resultado(repo))
            elif parsed.path == "/api/grafo":
                repo = params.get("repo", ["h3"])[0]
                grafo = params.get("grafo", ["integrado"])[0]
                limite = int(params.get("limite", ["80"])[0])
                self.send_json(preparar_grafo(repo, grafo, limite))
            elif parsed.path == "/api/pipeline/status":
                self.send_json(status_pipeline())
            else:
                self.send_json({"error": "Rota nao encontrada."}, status=404)
        except Exception as exc:
            traceback.print_exc()
            self.send_json({"error": str(exc)}, status=500)

    def do_POST(self):
        parsed = urlparse(self.path)
        tamanho = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(tamanho).decode("utf-8") if tamanho else "{}"

        try:
            payload = json.loads(raw)
            if parsed.path == "/api/pipeline/start":
                self.send_json(
                    iniciar_pipeline(
                        payload.get("repo", "h3"),
                        bool(payload.get("process_only", True)),
                        bool(payload.get("force", False)),
                    )
                )
            else:
                self.send_json({"error": "Rota nao encontrada."}, status=404)
        except Exception as exc:
            traceback.print_exc()
            self.send_json({"error": str(exc)}, status=500)


HTML = r"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TP_ES_GRAFOS - Visualizacao</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #eef2f7;
      --panel: #ffffff;
      --ink: #0f172a;
      --muted: #64748b;
      --line: #d8dee8;
      --blue: #2563eb;
      --green: #059669;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Arial, Helvetica, sans-serif;
      letter-spacing: 0;
    }
    header {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 16px;
      background: var(--panel);
      border-bottom: 1px solid var(--line);
      position: sticky;
      top: 0;
      z-index: 10;
    }
    h1 { margin: 0 18px 0 0; font-size: 18px; white-space: nowrap; }
    select, button, label {
      font-size: 14px;
    }
    select, button {
      height: 34px;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      border-radius: 6px;
      padding: 0 10px;
    }
    button.primary {
      background: var(--blue);
      color: #fff;
      border-color: var(--blue);
      font-weight: 700;
    }
    main { padding: 16px; }
    .status { margin-left: auto; color: var(--muted); font-size: 13px; }
    .tabs { display: flex; gap: 8px; margin-bottom: 12px; }
    .tab {
      border: 1px solid var(--line);
      background: var(--panel);
      padding: 9px 12px;
      border-radius: 6px;
      cursor: pointer;
    }
    .tab.active { background: var(--ink); color: #fff; }
    .view { display: none; }
    .view.active { display: block; }
    .cards {
      display: grid;
      grid-template-columns: repeat(4, minmax(150px, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }
    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 14px;
    }
    .card .label { color: var(--muted); font-size: 13px; }
    .card .value { font-size: 24px; font-weight: 700; margin-top: 6px; color: var(--blue); }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 12px;
      min-width: 0;
    }
    .panel h2 { margin: 0 0 10px 0; font-size: 16px; }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th, td {
      border-bottom: 1px solid #e5eaf1;
      padding: 7px 8px;
      text-align: left;
      vertical-align: top;
    }
    th { color: #334155; background: #f8fafc; position: sticky; top: 0; }
    .table-wrap { max-height: 360px; overflow: auto; border: 1px solid #edf1f6; }
    #graph {
      width: 100%;
      height: calc(100vh - 170px);
      min-height: 520px;
      background: #f8fafc;
      border: 1px solid var(--line);
      border-radius: 6px;
    }
    .graph-controls { display: flex; gap: 10px; align-items: center; margin-bottom: 10px; }
    pre {
      margin: 0;
      height: calc(100vh - 170px);
      min-height: 520px;
      overflow: auto;
      background: #0f172a;
      color: #e2e8f0;
      padding: 12px;
      border-radius: 6px;
      white-space: pre-wrap;
    }
    @media (max-width: 900px) {
      header { flex-wrap: wrap; }
      .status { margin-left: 0; width: 100%; }
      .cards, .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <h1>TP_ES_GRAFOS</h1>
    <label>Repositorio <select id="repo"><option value="h3">h3</option><option value="hyprland">hyprland</option></select></label>
    <label><input id="processOnly" type="checkbox" checked> Usar dados locais</label>
    <label><input id="force" type="checkbox"> Forcar coleta</label>
    <button class="primary" id="run">Executar pipeline</button>
    <button id="refresh">Atualizar</button>
    <span class="status" id="status">Inicializando...</span>
  </header>
  <main>
    <nav class="tabs">
      <button class="tab active" data-view="metricas">Metricas</button>
      <button class="tab" data-view="grafo">Grafo</button>
      <button class="tab" data-view="estrutura">Estrutura</button>
      <button class="tab" data-view="execucao">Execucao</button>
    </nav>

    <section id="metricas" class="view active">
      <div class="cards" id="cards"></div>
      <div class="panel">
        <h2>Resumo dos grafos</h2>
        <div class="table-wrap"><table id="resumo"></table></div>
      </div>
      <div class="grid" style="margin-top:12px">
        <div class="panel">
          <h2>Top centralidade</h2>
          <div class="table-wrap"><table id="centralidade"></table></div>
        </div>
        <div class="panel">
          <h2>Comunidades</h2>
          <div class="table-wrap"><table id="comunidades"></table></div>
        </div>
      </div>
    </section>

    <section id="grafo" class="view">
      <div class="graph-controls">
        <label>Grafo <select id="graphKind">
          <option value="comentarios">Comentarios</option>
          <option value="fechamentos">Fechamentos</option>
          <option value="reviews_merges">Reviews/Merges</option>
          <option value="integrado" selected>Integrado</option>
        </select></label>
        <span class="status">Amostra com os vertices mais conectados</span>
      </div>
      <canvas id="graph"></canvas>
    </section>

    <section id="estrutura" class="view">
      <div class="panel">
        <h2>Estrutura e coesao</h2>
        <div class="table-wrap"><table id="estruturaTable"></table></div>
      </div>
    </section>

    <section id="execucao" class="view">
      <pre id="logs"></pre>
    </section>
  </main>
  <script>
    const state = { resultado: null, graph: null };
    const $ = (id) => document.getElementById(id);

    function setStatus(text) { $("status").textContent = text; }
    function fmt(value) {
      if (value === null || value === undefined) return "-";
      if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(6);
      return String(value);
    }
    async function api(path, options) {
      const res = await fetch(path, options);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Erro na requisicao");
      return data;
    }
    function table(el, headers, rows) {
      el.innerHTML = "<thead><tr>" + headers.map(h => `<th>${h}</th>`).join("") + "</tr></thead>" +
        "<tbody>" + rows.map(row => "<tr>" + row.map(v => `<td>${fmt(v)}</td>`).join("") + "</tr>").join("") + "</tbody>";
    }
    async function loadData() {
      const repo = $("repo").value;
      setStatus(`Carregando ${repo}...`);
      state.resultado = await api(`/api/resultados?repo=${encodeURIComponent(repo)}`);
      renderMetrics();
      await loadGraph();
      setStatus(`Dados carregados: ${repo}`);
    }
    function renderMetrics() {
      const grafos = state.resultado.grafos;
      const totals = grafos.reduce((acc, g) => {
        acc.grafos += 1;
        acc.vertices += g.resumo.quantidade_vertices;
        acc.arestas += g.resumo.quantidade_arestas_nao_direcionadas;
        acc.peso += g.resumo.peso_total_interacoes;
        return acc;
      }, { grafos: 0, vertices: 0, arestas: 0, peso: 0 });
      $("cards").innerHTML = [
        ["Grafos", totals.grafos],
        ["Vertices somados", totals.vertices],
        ["Arestas nao dir.", totals.arestas],
        ["Peso total", fmt(totals.peso)]
      ].map(([label, value]) => `<div class="card"><div class="label">${label}</div><div class="value">${value}</div></div>`).join("");
      table($("resumo"), ["Grafo", "Vertices", "Arestas dir.", "Arestas nao dir.", "Peso", "Dens. dir.", "Dens. nao dir."],
        grafos.map(g => [g.nome_grafo, g.resumo.quantidade_vertices, g.resumo.quantidade_arestas_direcionadas,
          g.resumo.quantidade_arestas_nao_direcionadas, g.resumo.peso_total_interacoes,
          g.resumo.densidade_direcionada, g.resumo.densidade_nao_direcionada]));
      table($("centralidade"), ["Grafo", "#", "Usuario", "Grau", "Centralidade", "Entrada", "Saida", "Ponderado"],
        grafos.flatMap(g => g.top_5_centralidade.map((item, i) => [g.nome_grafo, i + 1, item.usuario, item.grau_total,
          item.centralidade_grau, item.grau_entrada, item.grau_saida, item.grau_ponderado])));
      table($("comunidades"), ["Grafo", "ID", "Tamanho", "Amostra"],
        grafos.flatMap(g => g.comunidades_detectadas.map(c => [g.nome_grafo, c.id_comunidade, c.tamanho, c.amostra_membros.join(", ")])));
      table($("estruturaTable"), ["Grafo", "Aglom. media", "Aglom. grau >= 2", "Assortatividade", "Densidade", "Aglomeracao", "Assortatividade"],
        grafos.map(g => {
          const m = g.metricas_estrutura_coesao || {};
          return [g.nome_grafo, m.coeficiente_aglomeracao_medio_todos_vertices,
            m.coeficiente_aglomeracao_medio_grau_maior_igual_2, m.assortatividade_por_grau,
            m.interpretacao_densidade, m.interpretacao_aglomeracao, m.interpretacao_assortatividade];
        }));
    }
    async function loadGraph() {
      const repo = $("repo").value;
      const grafo = $("graphKind").value;
      state.graph = await api(`/api/grafo?repo=${encodeURIComponent(repo)}&grafo=${encodeURIComponent(grafo)}&limite=80`);
      drawGraph();
    }
    function drawGraph() {
      const canvas = $("graph");
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * devicePixelRatio;
      canvas.height = rect.height * devicePixelRatio;
      const ctx = canvas.getContext("2d");
      ctx.scale(devicePixelRatio, devicePixelRatio);
      ctx.clearRect(0, 0, rect.width, rect.height);
      if (!state.graph) return;
      const nodes = state.graph.nodes.map(n => ({...n}));
      const links = state.graph.links;
      const w = rect.width, h = rect.height;
      const cx = w / 2, cy = h / 2, r = Math.min(w, h) * 0.35;
      nodes.forEach((n, i) => {
        const a = Math.PI * 2 * i / Math.max(nodes.length, 1);
        n.x = cx + Math.cos(a) * r;
        n.y = cy + Math.sin(a) * r;
      });
      const byId = new Map(nodes.map(n => [n.id, n]));
      for (let iter = 0; iter < 90; iter++) {
        for (const n of nodes) { n.vx = 0; n.vy = 0; }
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const a = nodes[i], b = nodes[j];
            let dx = a.x - b.x, dy = a.y - b.y, d = Math.max(Math.hypot(dx, dy), 1);
            const f = 900 / d;
            a.vx += dx / d * f; a.vy += dy / d * f;
            b.vx -= dx / d * f; b.vy -= dy / d * f;
          }
        }
        for (const l of links) {
          const a = byId.get(l.source), b = byId.get(l.target);
          if (!a || !b) continue;
          let dx = b.x - a.x, dy = b.y - a.y, d = Math.max(Math.hypot(dx, dy), 1);
          const f = (d - 120) * 0.018;
          a.vx += dx / d * f; a.vy += dy / d * f;
          b.vx -= dx / d * f; b.vy -= dy / d * f;
        }
        for (const n of nodes) {
          n.x = Math.max(24, Math.min(w - 24, n.x + n.vx));
          n.y = Math.max(24, Math.min(h - 24, n.y + n.vy));
        }
      }
      const maxWeight = Math.max(...nodes.map(n => n.weight), 1);
      const maxEdge = Math.max(...links.map(l => l.weight), 1);
      ctx.lineCap = "round";
      for (const l of links) {
        const a = byId.get(l.source), b = byId.get(l.target);
        if (!a || !b) continue;
        ctx.strokeStyle = "#cbd5e1";
        ctx.lineWidth = 1 + 4 * l.weight / maxEdge;
        ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
      }
      for (const n of nodes) {
        const radius = 6 + 17 * Math.sqrt(n.weight / maxWeight);
        ctx.fillStyle = "#2563eb";
        ctx.strokeStyle = "#0f172a";
        ctx.lineWidth = 1;
        ctx.beginPath(); ctx.arc(n.x, n.y, radius, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
        if (radius > 11) {
          ctx.fillStyle = "#0f172a";
          ctx.font = "bold 11px Arial";
          ctx.fillText(n.label.slice(0, 18), n.x + radius + 4, n.y + 4);
        }
      }
    }
    async function startPipeline() {
      const payload = {
      repo: $("repo").value,
        process_only: $("processOnly").checked,
        force: $("force").checked
      };
      const data = await api("/api/pipeline/start", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
      });
      setStatus(data.message);
      pollPipeline();
    }
    async function pollPipeline() {
      const data = await api("/api/pipeline/status");
      $("logs").textContent = data.logs || "";
      $("logs").scrollTop = $("logs").scrollHeight;
      if (data.running) {
        setStatus("Pipeline em execucao...");
        setTimeout(pollPipeline, 1000);
      } else if (data.returncode !== null) {
        setStatus(`Pipeline finalizado: ${data.returncode}`);
        if (data.returncode === 0) loadData();
      }
    }
    document.querySelectorAll(".tab").forEach(tab => {
      tab.addEventListener("click", () => {
        document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
        document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
        tab.classList.add("active");
        $(tab.dataset.view).classList.add("active");
        if (tab.dataset.view === "grafo") setTimeout(drawGraph, 50);
      });
    });
    const initialRepo = new URLSearchParams(window.location.search).get("repo");
    if (initialRepo && ["h3", "hyprland"].includes(initialRepo)) {
      $("repo").value = initialRepo;
    }
    $("repo").addEventListener("change", loadData);
    $("refresh").addEventListener("click", loadData);
    $("run").addEventListener("click", startPipeline);
    $("graphKind").addEventListener("change", loadGraph);
    window.addEventListener("resize", () => { if (document.querySelector("#grafo.active")) drawGraph(); });
    loadData().catch(err => { console.error(err); setStatus(err.message); });
    pollPipeline().catch(() => {});
  </script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Interface web local dos grafos.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    debug_log(f"Python={sys.version.split()[0]} executable={sys.executable}")
    debug_log(f"BASE_DIR={BASE_DIR}")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}"
    debug_log(f"Servidor iniciado em {url}")
    print(f"\nAbra no navegador: {url}\n", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        debug_log("Encerrando servidor")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
