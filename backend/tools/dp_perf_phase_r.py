# -*- coding: utf-8 -*-
"""Phase R4 — Retrieval/Runtime 性能回归测量（2026-08-30）

三个独立子进程场景（各自干净内存账, 结果 JSON 行输出, 父进程汇总）:

  general    冷启动（import main）+ General 首请求（search_books, 记录 retrieval_mode）
  nietzsche  Nietzsche 冷路径: persona-only 域加载 → corpus 混合检索 → graph → 10 轮会话
             （逐步记录 private/rss; 验证 persona-only 不加载 453MB corpus、无无界增长）
  legacy     旧行为基线（RAM_BEFORE 代理）: 旧 load_bundle 全量加载（含 453MB all_chunks.json）
             + 旧 term-count 语料查询——与优化后 nietzsche 场景同题对比

用法: .venv/Scripts/python.exe backend/tools/dp_perf_phase_r.py [general|nietzsche|legacy|all]
结果落盘: backend/data/phase_r_perf.json（gitignore 目录）
"""
import json
import os
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent          # backend/
sys.path.insert(0, str(BASE))
DATA = BASE / "data"
OUT_FILE = DATA / "phase_r_perf.json"

CORPUS_QUERIES = ["权力意志", "永恒轮回与相同者的永恒回归", "凝视深渊时深渊也在凝视你"]
SESSION_TURNS = [
    ("philosopher_memory", {"question": "尼采什么时候开始头痛"}),
    ("philosopher_corpus", {"query": "上帝之死与虚无主义"}),
    ("philosopher_graph", {"concept": "权力意志"}),
    ("philosopher_concepts", {"concept": "永恒轮回"}),
    ("philosopher_user", {"question": "超人是不是种族优越"}),
    ("search_books", {"query": "尼采 永恒轮回", "limit": 5}),
]


def _mem():
    import psutil
    mi = psutil.Process().memory_info()
    return {"private_mb": round(mi.private / 1e6, 1), "rss_mb": round(mi.rss / 1e6, 1)}


def _tool(tool_name, args):
    """与生产一致的 philosopher 工具执行（agents.make_philo_tool / TOOLS 注册表）"""
    import routes.agent as AG
    if tool_name.startswith("philosopher_"):
        import agents
        return agents.make_philo_tool("nietzsche", tool_name)(args)
    return AG.TOOLS[tool_name]["execute"](args)


def _evidence_count(result):
    if not isinstance(result, dict):
        return 0
    return len(result.get("echoes") or result.get("results") or result.get("memories") or
               result.get("entities") or result.get("concepts") or [])


def run_general():
    out = {"scenario": "general"}
    t0 = time.time()
    import main            # backend/main.py: FastAPI app + 全部路由/工具注册
    out["cold_startup_s"] = round(time.time() - t0, 2)
    out["mem_after_import"] = _mem()
    t1 = time.time()
    r = _tool("search_books", {"query": "存在主义 萨特 自由选择", "limit": 5})
    out["first_search"] = {"latency_s": round(time.time() - t1, 2),
                           "mode": (r or {}).get("method"),
                           "results": _evidence_count(r),
                           "degraded_reason": (r or {}).get("degraded_reason", "")}
    out["mem_after_first_request"] = _mem()
    print("RESULT " + json.dumps(out, ensure_ascii=False))


def run_nietzsche():
    import agents
    out = {"scenario": "nietzsche"}
    t0 = time.time()
    import routes.agent    # 与生产一致的加载面（.env/工具注册表）
    out["cold_startup_s"] = round(time.time() - t0, 2)
    out["mem_after_import"] = _mem()

    # persona-only 路径（不触 corpus/graph/memory 的工具）
    t1 = time.time()
    r_style = _tool("philosopher_style", {})
    r_concept = _tool("philosopher_concepts", {"concept": "权力意志"})
    out["persona_only"] = {"latency_s": round(time.time() - t1, 2),
                           "evidence": _evidence_count(r_style) + _evidence_count(r_concept),
                           "domains_loaded": agents.loaded_domains("nietzsche")}
    out["mem_after_persona_only"] = _mem()

    # corpus 混合检索（首次 = 索引懒加载计入延迟）
    corpus = []
    for q in CORPUS_QUERIES:
        t2 = time.time()
        r = _tool("philosopher_corpus", {"query": q})
        corpus.append({"query": q, "latency_s": round(time.time() - t2, 2),
                       "mode": (r.get("retrieval") or {}).get("mode"),
                       "lex_scope": (r.get("retrieval") or {}).get("lex_scope"),
                       "evidence": _evidence_count(r),
                       "degraded": (r.get("retrieval") or {}).get("degraded_reason", "")})
    out["corpus_retrieval"] = corpus
    out["mem_after_corpus"] = _mem()

    # graph 检索
    t3 = time.time()
    r = _tool("philosopher_graph", {"concept": "永恒轮回"})
    out["graph_retrieval"] = {"latency_s": round(time.time() - t3, 2),
                              "evidence": _evidence_count(r)}
    out["mem_after_graph"] = _mem()

    # memory 域（首次加载）
    t4 = time.time()
    _tool("philosopher_memory", {"question": "尼采 生病"})
    out["memory_first"] = {"latency_s": round(time.time() - t4, 2)}
    out["mem_after_memory"] = _mem()

    # 10 轮会话: 内存轨迹（无界增长检查）
    trace = []
    for i in range(10):
        name, args = SESSION_TURNS[i % len(SESSION_TURNS)]
        t5 = time.time()
        _tool(name, args)
        m = _mem()
        m.update({"turn": i + 1, "tool": name, "latency_s": round(time.time() - t5, 2)})
        trace.append(m)
    out["session_10_turns"] = trace
    private_trace = [t["private_mb"] for t in trace]
    out["session_growth_mb"] = round(max(private_trace) - min(private_trace), 1)
    out["mem_final"] = _mem()
    print("RESULT " + json.dumps(out, ensure_ascii=False))


def run_legacy():
    """旧行为基线（RAM_BEFORE 代理）: 旧 load_bundle 全量 json.load + 旧 term-count 语料查询"""
    import agents
    out = {"scenario": "legacy_before"}
    t0 = time.time()
    import routes.agent
    out["cold_startup_s"] = round(time.time() - t0, 2)
    out["mem_after_import"] = _mem()

    # 复刻旧 load_bundle: 一次性加载全部 bundle 文件（含 453MB all_chunks.json）
    spec = agents.PHILO_AGENTS["nietzsche"]["bundle"]
    t1 = time.time()
    b = {}
    for key, path in spec.items():
        if path and Path(path).exists():
            b[key] = json.load(open(path, encoding="utf-8"))
    out["bundle_full_load_s"] = round(time.time() - t1, 2)
    out["mem_after_full_bundle"] = _mem()      # ≈ RAM_BEFORE（warm Nietzsche）

    # 旧 philosopher_corpus 语义: 全量 term-count 扫描
    import re
    legacy = []
    for q in CORPUS_QUERIES:
        t2 = time.time()
        terms = [t for t in re.split(r"[\s,，。；;：:、]+", q[:50]) if len(t) >= 2]
        scored = []
        for c in b.get("corpus") or []:
            text = c.get("text", "")
            s = sum(text.count(t) for t in terms)
            if s > 0:
                scored.append((s, c))
        scored.sort(key=lambda x: -x[0])
        legacy.append({"query": q, "latency_s": round(time.time() - t2, 2),
                       "evidence": len(scored[:3])})
    out["corpus_retrieval_legacy"] = legacy
    out["mem_final"] = _mem()
    print("RESULT " + json.dumps(out, ensure_ascii=False))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    runners = {"general": run_general, "nietzsche": run_nietzsche, "legacy": run_legacy}
    if mode != "all":
        runners[mode]()
        return
    results = {}
    import subprocess
    for name in ("general", "nietzsche", "legacy"):
        print(f"=== scenario {name} ===", flush=True)
        proc = subprocess.run([sys.executable, os.path.abspath(__file__), name],
                              capture_output=True, text=True, cwd=str(BASE))
        for line in proc.stdout.splitlines():
            if line.startswith("RESULT "):
                r = json.loads(line[7:])
                results[name] = r
                print(json.dumps(r, ensure_ascii=False, indent=1)[:2200])
        if proc.returncode != 0:
            print(f"[{name}] FAILED rc={proc.returncode}\n{proc.stderr[-1500:]}")
            results[name] = {"error": proc.stderr[-500:]}
    try:
        DATA.mkdir(exist_ok=True)
        OUT_FILE.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"saved -> {OUT_FILE}")
    except Exception as e:
        print(f"save failed: {e}")


if __name__ == "__main__":
    main()
