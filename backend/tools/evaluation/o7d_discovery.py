# -*- coding: utf-8 -*-
"""O7-D §12/§28-29: Live discovery run —— 每 cluster 跑 manifest 查询,
Crossref+OpenAlex → canonical dedup → candidate pool, 输出冻结 snapshot。

DISCOVERY RUN 与 REGISTRY BUILD 分离（网络结果会漂移; registry 从 frozen
snapshot 确定性重建）。

用法: SCHOLARLY_NETWORK_MODE=TRUSTED_PROXY .venv/bin/python backend/tools/evaluation/o7d_discovery.py
"""
import hashlib
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))

import scholarly_sources as SS

MANIFEST = os.path.join(ROOT, "docs/evidence/PHIAGENT_O7D_COVERAGE_MANIFEST.json")
OUT = os.path.join(ROOT, "docs/evidence", "PHIAGENT_O7D_DISCOVERY_SNAPSHOT.json")
PER_CLUSTER_CAP = 14   # 候选池上限（去重后按引用数排序）


def discover():
    m = json.load(open(MANIFEST, encoding="utf-8"))
    snapshot = {"version": "o7d-1", "manifest_version": m["version"],
                "ran_at": int(time.time()), "mode": "DISCOVERY_RUN",
                "network_mode": SS._network_mode(),
                "clusters": {}, "errors": []}
    for c in m["clusters"]:
        cid = c["cluster_id"]
        # 直接取 provider 级记录（search_scholarship 返回的是已合并 canonical,
        # 重复 merge 会破坏结构）——snapshot 层面统一 dedup 一次
        records, errs = [], []
        for q in c["queries"]:
            for name, fn in (("crossref", SS.search_crossref), ("openalex", SS.search_openalex)):
                got = None
                for attempt in range(4):        # 429 退避重试（礼貌间隔）
                    try:
                        got = fn(q, limit=8)
                        break
                    except SS.ProviderError as e:
                        if e.kind == "PROVIDER_RATE_LIMIT" and attempt < 3:
                            time.sleep(2.5 * (attempt + 1))
                            continue
                        errs.append({"query": q, "provider": name,
                                     "error": e.kind, "detail": e.detail})
                        break
                    except Exception as e:
                        errs.append({"query": q, "provider": name, "error": str(e)})
                        break
                if got:
                    records.extend(got)
            time.sleep(1.0)                     # cluster 间礼貌间隔
        canon = SS.merge_records(records)
        canon.sort(key=lambda r: -max((p.get("cited_by") or 0)
                                      for p in r["provider_records"]))
        snapshot["clusters"][cid] = {
            "group": c["group"], "topic": c["topic"],
            "queries": c["queries"],
            "candidates": canon[:PER_CLUSTER_CAP],
        }
        snapshot["errors"].extend(errs)
        print(f"  {cid}: {len(canon[:PER_CLUSTER_CAP])} candidates, "
              f"{len(c['queries'])} queries, {len(errs)} errors")
    uniq = {}
    for cid, cl in snapshot["clusters"].items():
        for r in cl["candidates"]:
            uniq.setdefault(r["source_record_id"], r)
    snapshot["unique_canonical_records"] = len(uniq)
    blob = json.dumps(snapshot, ensure_ascii=False, sort_keys=True).encode()
    snapshot["discovery_snapshot_hash"] = hashlib.sha256(blob).hexdigest()
    json.dump(snapshot, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"clusters": len(snapshot["clusters"]),
                      "unique_canonical_records": len(uniq),
                      "errors": len(snapshot["errors"]),
                      "discovery_snapshot_hash": snapshot["discovery_snapshot_hash"][:16]},
                     ensure_ascii=False))


if __name__ == "__main__":
    discover()
