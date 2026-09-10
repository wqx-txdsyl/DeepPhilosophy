# -*- coding: utf-8 -*-
"""O7-E V3-RP3 §3: registry alias/index 覆盖恢复——最小 curated 扩充。

新增 3 条王阳明 scholarly records（Live OpenAlex provenance, METADATA_ONLY）+
全部相关记录的多语 alias 字段; 重建 FTS 索引（aliases 列）。
零 semantic router/零 quota/零 eval 信息进入 production。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))

REG_PATH = os.path.join(ROOT, "backend", "data", "scholarly", "registry.jsonl")
IDX = os.path.join(ROOT, "backend", "data", "scholarly", "index.sqlite")

NEW_SIDS = ["doi:10.1111/1540-6253.12204",
            "doi:10.14711/thesis-991012644164903412",
            "doi:10.1007/978-3-476-05728-0_21974-1"]

WY_ALIASES = ["王阳明", "Wang Yangming", "王守仁", "阳明学", "心学", "知行合一",
              "致良知", "格物", "gewu", "investigation of things",
              "unity of knowledge and action", "宋明理学", "Neo-Confucianism"]
ZHU_ALIASES = ["朱熹", "朱子", "Zhu Xi", "朱子学", "理學", "宋明理学",
               "Neo-Confucianism", "格物"]


def relevant(r):
    import re
    s = json.dumps(r, ensure_ascii=False)
    return bool(re.search("王阳明|Yangming|Wang Shouren|朱熹|朱子|Zhu Xi|理學|理学", s))


def main():
    rows = [json.loads(l) for l in open(REG_PATH, encoding="utf-8") if l.strip()]
    cache = json.load(open(os.path.join(ROOT, "backend", "data",
                                        "scholarly_cache.json"),
                           encoding="utf-8")).get("records") or {}
    by_id = {r.get("source_record_id"): r for r in rows}

    added, aliased = [], []
    for sid in NEW_SIDS:
        src = cache.get(sid)
        if not src:
            print("skip(无缓存):", sid)
            continue
        if sid in by_id:
            print("skip(已存在):", sid)
            continue
        rec = dict(src)
        rec["cluster_ids_accepted"] = ["wang-yangming-zhixingheyi",
                                       "song-ming-confucianism"]
        rec["aliases"] = WY_ALIASES
        rows.append(rec)
        by_id[sid] = rec
        added.append(sid)

    # 既有相关记录的 alias 富集（朱熹/宋明理学/王阳明概念族）
    for r in rows:
        if r.get("source_record_id") in NEW_SIDS:
            continue
        if not relevant(r):
            continue
        cur = set(r.get("aliases") or [])
        aliases = ZHU_ALIASES if r.get("code", "") or "朱" in json.dumps(
            r, ensure_ascii=False) else WY_ALIASES
        cur.update(aliases)
        r["aliases"] = sorted(cur)
        aliased.append(r.get("source_record_id"))

    with open(REG_PATH, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 重建 FTS 索引（含 aliases 列）
    import scholarly_registry as SR
    import importlib
    importlib.reload(SR)
    if os.path.exists(SR.INDEX):
        os.unlink(SR.INDEX)
    n = SR.build_index()
    print(f"registry: {len(rows)} 条 (新增 {len(added)}, alias 富集 {len(aliased)}); "
          f"FTS indexed: {n}")
    return len(added), len(aliased), len(rows), n


if __name__ == "__main__":
    main()
