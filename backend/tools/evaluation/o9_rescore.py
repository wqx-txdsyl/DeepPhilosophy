# -*- coding: utf-8 -*-
"""O9-R1 §1: provider-blind graded relevance rubric（evaluation-only）。

冻结 rubric: 对每条 Top-K record 依据 query + relevance_note + title + abstract/summary
+ 书目元数据做分级判断 2=直接相关 / 1=部分或支撑相关 / 0=不相关。
judge 固定 temperature=0, 不暴露 provider 名称。逐 record 保存 judgment+reason。
A=Crossref 用已保存 raw results 离线重算（不重调 API）。
产出 backend/tools/_tmp/o9_rescored.json（增量）。
"""
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
TMP = os.path.join(ROOT, "backend/tools/_tmp")
EVID = os.path.join(ROOT, "docs/evidence")

RUBRIC = """你是学术检索评估的独立评分器（provider-blind: 你不知道结果来自哪个 provider）。
对给定的「查询」与「候选文献」逐条打分（0-2 整数）:
2 = directly relevant: 文献直接处理查询所问的主题/文本/争论
1 = partially/supportingly relevant: 部分相关（相邻主题/提供背景/覆盖查询的一个子题）
0 = irrelevant: 与查询主题无实质关系（仅字面词命中）
输出 JSON: {"judgments": [{"idx": 0, "score": 0-2, "reason": "一句话中文"}, ...]}
逐条独立评分; 不奉承不放宽; 中文与英文文献同标准。"""

SYS = RUBRIC


def call_judge(prompt, _key):
    payload = {"model": "glm-4.6", "temperature": 0, "max_tokens": 3000,
               "thinking": {"type": "disabled"},
               "response_format": {"type": "json_object"},
               "messages": [{"role": "system", "content": SYS},
                            {"role": "user", "content": prompt}]}
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + (_key or "")})
    with urllib.request.urlopen(req, timeout=240) as r:
        outer = json.loads(r.read())
    return outer["choices"][0]["message"]["content"]


def record_brief(idx, rec):
    return {"idx": idx, "title": (rec.get("title") or "")[:160],
            "authors": [a.get("name") for a in (rec.get("authors") or [])][:3]
            if isinstance(rec.get("authors"), list) else None,
            "year": rec.get("publication_year"),
            "container": rec.get("container_title"),
            "abstract": (rec.get("abstract_text") or "")[:420]}


def main():
    _key = None
    for line in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
        if line.strip().startswith("ZHIPU_API_KEY="):
            _key = line.split("=", 1)[1].strip().strip('"').strip("'")
            break
    raw = json.load(open(os.path.join(TMP, "o9_provider_results.json"), encoding="utf-8"))
    qs = json.load(open(os.path.join(EVID, "O9_QUERYSET.json"), encoding="utf-8"))
    notes = {c["query_id"]: c.get("relevance_note", "") for c in qs["cases"]}
    out_path = os.path.join(TMP, "o9_rescored.json")
    res = []
    if os.path.exists(out_path):
        res = json.load(open(out_path, encoding="utf-8"))
    done = {r["query_id"] for r in res}
    for row in raw:
        qid = row["query_id"]
        if qid in done:
            continue
        recs = row["providers"]["A_crossref"]["raw"]
        briefs = [record_brief(i, r) for i, r in enumerate(recs)]
        prompt = (f"[query] {row['query']}\n[relevance_note] {notes.get(qid,'')}\n"
                  f"[candidates]\n" + json.dumps(briefs, ensure_ascii=False))
        entry = {"query_id": qid, "provider": "A_crossref", "judgments": None}
        try:
            content = call_judge(prompt, _key)
            parsed = json.loads(content)
            entry["judgments"] = parsed.get("judgments")
            entry["status"] = "OK"
        except Exception as e:
            entry["status"] = "ERROR"
            entry["error"] = str(e)[:200]
        res = [x for x in res if x["query_id"] != qid] + [entry]
        json.dump(res, open(out_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        n_ok = sum(1 for j in (entry["judgments"] or []))
        print(f"== rescored {qid}: {entry['status']} ({n_ok} judgments)", flush=True)
    print("RESCORE DONE", len(res))


if __name__ == "__main__":
    main()
