# -*- coding: utf-8 -*-
"""O7-D §13-14: Corpus curation——glm-4.6 evaluation-only 相关性判定。

对每个 (cluster, candidate record) 判 TOPICAL_RELEVANCE 0-4。
输入只有 cluster 主题 + title + abstract(如有) + 出版元数据——
judge 无权补作者/DOI/年份/改 title。
relevance>=3 → 该 cluster 的 accepted set; 低相关记录保留为 DISCOVERY_ONLY。

用法: SCHOLARLY_NETWORK_MODE=TRUSTED_PROXY .venv/bin/python backend/tools/evaluation/o7d_curation.py
"""
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))

SNAP = os.path.join(ROOT, "docs/evidence", "PHIAGENT_O7D_DISCOVERY_SNAPSHOT.json")
OUT = os.path.join(ROOT, "docs/evidence", "PHIAGENT_O7D_CURATION_DECISIONS.json")

_key = None
for line in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
    if line.strip().startswith("ZHIPU_API_KEY="):
        _key = line.split("=", 1)[1].strip().strip('"').strip("'")

SYS = ("You are a corpus curation relevance assessor for philosophy research "
       "clusters. Given a research cluster topic and a scholarly record (title, "
       "abstract if available, publication metadata), score TOPICAL_RELEVANCE "
       "0-4: 0=unrelated, 1=vaguely connected, 2=same broad area, 3=directly on "
       "topic, 4=centrally on the exact question. You may NOT invent or correct "
       "any bibliographic field. Output JSON only: "
       '{"TOPICAL_RELEVANCE": <int 0-4>, "reason": "<=30 words"}')


def call_judge(prompt):
    payload = {"model": "glm-4.6", "temperature": 0, "max_tokens": 300,
               "thinking": {"type": "disabled"},
               "response_format": {"type": "json_object"},
               "messages": [{"role": "system", "content": SYS},
                            {"role": "user", "content": prompt}]}
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + (_key or "")})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"] or ""


def main():
    snap = json.load(open(SNAP, encoding="utf-8"))
    decisions = []
    if os.path.exists(OUT):   # 断点续跑
        decisions = json.load(open(OUT, encoding="utf-8"))["decisions"]
    done = {(d["cluster_id"], d["source_record_id"]) for d in decisions}
    total = sum(len(c["candidates"]) for c in snap["clusters"].values())
    n = len(decisions)
    for cid, cl in snap["clusters"].items():
        for r in cl["candidates"]:
            if (cid, r["source_record_id"]) in done:
                continue
            ab = (r.get("abstract") or {}).get("text") or ""
            prompt = (f"CLUSTER TOPIC: {cl['topic']}\n"
                      f"TITLE: {r.get('title')}\n"
                      f"YEAR: {r.get('publication_year')} | TYPE: {r.get('publication_type')} "
                      f"| VENUE: {r.get('container_title')}\n"
                      f"ABSTRACT: {ab[:700]}")
            score = None
            for attempt in range(3):
                try:
                    out = json.loads(call_judge(prompt))
                    score = int(out.get("TOPICAL_RELEVANCE", 0))
                    break
                except Exception:
                    time.sleep(2 * (attempt + 1))
            decisions.append({"cluster_id": cid,
                              "source_record_id": r["source_record_id"],
                              "TOPICAL_RELEVANCE": score,
                              "judge": "glm-4.6"})
            n += 1
            if n % 25 == 0:
                print(f"  {n}/{total} judged", flush=True)
                json.dump({"version": "o7d-1", "decisions": decisions},
                          open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"version": "o7d-1", "decisions": decisions},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    acc = sum(1 for d in decisions if (d["TOPICAL_RELEVANCE"] or 0) >= 3)
    print(json.dumps({"judged": len(decisions), "accepted_pairs": acc,
                      "null_scores": sum(1 for d in decisions if d["TOPICAL_RELEVANCE"] is None)},
                     ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
