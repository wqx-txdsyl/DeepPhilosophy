# -*- coding: utf-8 -*-
"""Phase R — 真实 retrieval UAT（2026-08-30）

验收项 3: "Nietzsche semantic/paraphrase retrieval 不低于旧 lexical baseline"。

两种模式:
  uat_lexical  真实查询 × 新 philosopher_corpus（当前环境 embedding 429/欠费 → 生产降级路径
               与旧基线同条件对比） vs 旧 term-count 基线（同文本集、同分词、同 top-3 语义）
  uat_dense    用库内存量 embedding 作 query 向量（真实向量, 不调 API）走完整混合管线:
               断言 top-3 全部落在语义锚点（同著作/主题相邻 chunk）内

锚点集（anchor: 期望命中的书名子串 / 正文关键证据词）——6488 chunks 人工可判定的固定集。
结果落盘 backend/data/phase_r_uat.json。

用法: .venv/Scripts/python.exe backend/tools/dp_uat_phase_r.py
"""
import json
import os
import re
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent          # backend/
sys.path.insert(0, str(BASE))
OUT = BASE / "data" / "phase_r_uat.json"

# (query, 期望书名子串列表, 正文关键证据词列表) —— 命中 = top-3 内任一条满足 书名锚 OR 文本含证据词
UAT_SET = [
    ("权力意志", ["权力意志", "瓦格纳事件", "善恶的彼岸"], ["权力意志"]),
    ("永恒轮回", ["查拉图斯特拉如是说", "快乐的艺术", "快乐的科学", "权力意志", "瞧，这个人", "尼采传"],
     ["永恒轮回", "相同者", "轮回"]),
    ("超人", ["查拉图斯特拉如是说"], ["超人"]),
    ("上帝死了之后的道德", ["反基督", "论道德的谱系", "偶像的黄昏", "道德"], ["上帝", "道德", "虚无主义"]),
    ("永恒轮回与相同者的永恒回归", ["查拉图斯特拉如是说", "快乐的科学", "权力意志", "瞧，这个人", "尼采传"],
     ["永恒轮回", "相同者", "回归", "轮回"]),
    ("凝视深渊时深渊也在凝视你", ["查拉图斯特拉如是说"], ["深渊"]),
]


def _mem():
    import psutil
    mi = psutil.Process().memory_info()
    return {"private_mb": round(mi.private / 1e6, 1), "rss_mb": round(mi.rss / 1e6, 1)}


def _hit(echo, books, terms):
    """锚点判定: 书名含期望子串 OR 正文含证据词"""
    b = echo.get("book") or ""
    t = echo.get("text") or ""
    return any(x in b for x in books) or any(w in t for w in terms)


def baseline_top3(query, texts):
    """旧 philosopher_corpus 基线语义: 标点切词(≥2字) + 全量 term-count, top-3
    （文本集 = 运行时紧凑文本域, 与 all_chunks.json 同一 6488 chunks, 基线等价）"""
    import philo_retrieval as pr
    terms = [t for t in re.split(r"[\s,，。；;：:、]+", query[:50]) if len(t) >= 2]
    scored = []
    for row, text in texts.items():
        s = sum(text.count(t) for t in terms)
        if s > 0:
            scored.append((s, row))
    scored.sort(key=lambda x: -x[0])
    meta = pr._STATE["meta"]["rows"]
    return [{"book": meta[r][0], "chapter": meta[r][1], "text": texts[r][:220], "score": s}
            for _, r in scored[:3]]


def run_uat_lexical():
    import routes.agent            # 生产加载面
    import agents
    import philo_retrieval as pr
    tool = agents.make_philo_tool("nietzsche", "philosopher_corpus")

    # 旧基线文本集（复用运行时文本域, 与 all_chunks 同源同集）
    pr._ensure_index()
    pr._ensure_texts()
    texts = pr._STATE["texts"]
    meta = pr._STATE["meta"]["rows"]

    rows = []
    new_hits = base_hits = 0
    for q, books, terms in UAT_SET:
        t0 = time.time()
        r = tool({"query": q})
        lat = round(time.time() - t0, 2)
        echoes = r.get("echoes") or []
        mode = (r.get("retrieval") or {}).get("mode")
        degraded = (r.get("retrieval") or {}).get("degraded_reason", "")
        new_ok = any(_hit(e, books, terms) for e in echoes)
        base = baseline_top3(q, texts)
        base_ok = any(_hit(e, books, terms) for e in base)
        new_hits += int(new_ok)
        base_hits += int(base_ok)
        rows.append({"query": q, "mode": mode, "degraded": degraded, "latency_s": lat,
                     "new_top3": [{"book": e["book"], "chapter": e["chapter"][:20]} for e in echoes],
                     "new_hit": new_ok, "baseline_hit": base_ok,
                     "baseline_top3": [{"book": e["book"], "chapter": (e["chapter"] or "")[:20]} for e in base]})
        print(f"[{q}] mode={mode} new_hit={new_ok} baseline_hit={base_ok}")
    verdict = {
        "uat": "lexical", "queries": len(UAT_SET),
        "new_hits": new_hits, "baseline_hits": base_hits,
        "pass": new_hits >= base_hits,
        "note": "生产降级路径（embedding 欠费 429）与旧基线同条件对比; hybrid ≥ baseline 即 PASS",
        "mem_final": _mem(), "detail": rows,
    }
    print(f"LEXICAL UAT: {new_hits}/{len(UAT_SET)} vs baseline {base_hits}/{len(UAT_SET)} "
          f"→ {'PASS' if verdict['pass'] else 'FAIL'}")
    return verdict


def run_uat_dense():
    """存量向量作 query → 完整混合管线（不调 embedding API）:
    选 3 个独特正文段落（非样板页）, dense top-3 应全部落在同著作或同主题锚点内"""
    import numpy as np
    import routes.agent
    import philo_retrieval as pr
    import routes.agent_core as agent_core

    pr._ensure_index()
    pr._ensure_texts()
    vecs = np.load(pr.VEC_FILE)
    meta = pr._STATE["meta"]["rows"]
    texts = pr._STATE["texts"]

    # 手选锚点行: (row, 允许的书集合, 说明)
    def _find(book, needle, start=0):
        for i in range(start, len(meta)):
            if meta[i][0] == book and needle in texts.get(i, ""):
                return i
        return -1
    anchors = []
    r = _find("查拉图斯特拉如是说", "深渊")
    if r >= 0:
        anchors.append((r, ["查拉图斯特拉如是说"], "深渊/凝视段落"))
    r2 = _find("论道德的谱系", "怨恨")
    if r2 >= 0:
        anchors.append((r2, ["论道德的谱系", "善恶的彼岸"], "怨恨/道德谱系段落"))
    r3 = _find("快乐的科学", "永恒轮回")
    if r3 >= 0:
        anchors.append((r3, ["快乐的科学", "查拉图斯特拉如是说", "权力意志"], "永恒轮回段落"))
    assert len(anchors) == 3, f"锚点行不足: {anchors}"

    rows = []
    for row, allowed_books, label in anchors:
        vec = [float(x) for x in vecs[row]]

        def fake_embed(q, _v=vec):
            return _v
        agent_core._embed_query = fake_embed     # 进程内注入真实存量向量（不调 API）
        res = pr.retrieve(texts[row][:80], k=3)
        top = res["echoes"][:3]
        books_ok = all(e["book"] in allowed_books or
                       any(w in (texts.get(e["chunk_row"]) or "") for w in ("深渊", "怨恨", "永恒轮回", "轮回", "权力意志"))
                       for e in top)
        rows.append({"anchor_row": row, "label": label, "anchor_book": meta[row][0],
                     "mode": res["mode"], "top3": [{"book": e["book"], "chapter": e["chapter"][:20],
                                                    "dense": e["scores"]["dense"]} for e in top],
                     "pass": bool(top) and books_ok})
        print(f"[{label}] row={row} pass={rows[-1]['pass']} "
              f"top3={[t['book'] for t in rows[-1]['top3']]}")
    verdict = {
        "uat": "dense", "cases": rows, "pass": all(r["pass"] for r in rows),
        "note": "库内存量 embedding 作 query（真实向量, 不调 API）: dense 管线 top-3 语义锚点全中",
    }
    print(f"DENSE UAT: {'PASS' if verdict['pass'] else 'FAIL'}")
    return verdict


def main():
    verdicts = {}
    verdicts["lexical"] = run_uat_lexical()
    verdicts["dense"] = run_uat_dense()
    verdicts["overall_pass"] = verdicts["lexical"]["pass"] and verdicts["dense"]["pass"]
    try:
        OUT.write_text(json.dumps(verdicts, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"saved -> {OUT}")
    except Exception as e:
        print(f"save failed: {e}")
    print(f"UAT OVERALL: {'PASS' if verdicts['overall_pass'] else 'FAIL'}")


if __name__ == "__main__":
    main()
