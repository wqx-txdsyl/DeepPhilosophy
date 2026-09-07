# -*- coding: utf-8 -*-
"""O7-E RP2 Closure H/I + Bakeoff §2: canonical primary-truth mechanical evaluator（evaluation-only）。

唯一实现 = evaluate_primary_targets(case, read_chapters)。
所有入口（primary_satisfied/check_case/测试/Final Gate）共用本实现。
BOOK 目标: book_id 命中即读; BOOK_SUBWORK 合集目标: book_id + chapter_idx ∈
manifest 的 resolved_chapter_indices。生产 runtime 零 semantic router。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_MANIFEST = os.path.join(ROOT, "docs/evidence",
                         "PHIAGENT_O7E_RP2_PRIMARY_TARGET_RESOLUTION.json")


def _load_resolution_manifest(case_id):
    extra, subwork = {}, {}
    if os.path.exists(_MANIFEST):
        for x in json.load(open(_MANIFEST, encoding="utf-8")):
            if not isinstance(x, dict) or x.get("case_id") != case_id:
                continue
            if x.get("resolved_book_ids"):
                extra[(x.get("author"), x.get("work"))] = x["resolved_book_ids"]
            if x.get("identity_scope") == "BOOK_SUBWORK":
                subwork[x.get("work")] = x
    return extra, subwork


def evaluate_primary_targets(case, read_chapters):
    """唯一 primary-target 匹配核心。

    read_chapters: ["book_id#chapter_idx", ...]（EvidenceState 机械事实）。"""
    targets = case.get("primary_targets") or []
    if not targets:
        return None
    mode = case.get("primary_target_mode", "ANY")
    pairs = set()
    for r in read_chapters or []:
        b, _, c = str(r).partition("#")
        pairs.add((b, c))
    read_book_ids = {b for b, _ in pairs}
    extra, subwork = _load_resolution_manifest(case.get("case_id"))
    hits = 0
    for t in targets:
        work = (t.get("works") or [""])[0]
        ids = set(t.get("book_ids") or [])
        ids |= set(extra.get((t.get("author"), work), []))
        sw = subwork.get(work)
        if sw:
            chaps = set(sw.get("resolved_chapter_indices") or [])
            ok = any(b == sw.get("resolved_book_id")
                     and c.lstrip("-").isdigit() and int(c) in chaps
                     for b, c in pairs)
        else:
            ok = bool(ids & read_book_ids)
        if ok:
            hits += 1
    if mode == "ALL":
        return hits == len(targets)
    return hits >= 1


def primary_satisfied(case, tool_log):
    """兼容入口: tool_log → read_chapters → evaluate_primary_targets（唯一实现）。"""
    targets = case.get("primary_targets") or []
    if not targets:
        return None
    rc = []
    for t in tool_log or []:
        if (t.get("name") or "") != "get_chapter":
            continue
        rf = t.get("result_full")
        if isinstance(rf, dict) and rf.get("text") and not rf.get("error"):
            bid = (t.get("args") or {}).get("book_id") or rf.get("book_id")
            cidx = (t.get("args") or {}).get("chapter_idx", 0)
            if bid:
                rc.append(f"{bid}#{cidx}")
    return evaluate_primary_targets(case, rc)


def check_case(case, run):
    """Final Gate 单案例 primary 检查（唯一实现 = evaluate_primary_targets）。"""
    targets = case.get("primary_targets") or []
    if not targets:
        return {"primary_required": False}
    ev = run.get("evidence_digest") or {}
    facts = ev.get("facts") or {}
    rc = [str(x) for x in (facts.get("read_chapters") or [])] if isinstance(facts, dict) else []
    mode = case.get("primary_target_mode", "ANY")
    extra, subwork = _load_resolution_manifest(case.get("case_id"))
    resolved, read_ids, missing = [], [], []
    satisfied = evaluate_primary_targets(case, rc)
    for t in targets:
        work = (t.get("works") or [""])[0]
        ids = set(t.get("book_ids") or []) | set(extra.get((t.get("author"), work), []))
        resolved.append({"author": t.get("author"), "works": t.get("works"),
                         "book_ids": sorted(ids),
                         "identity_scope": "BOOK_SUBWORK" if work in subwork else "BOOK"})
        if ids:
            read_ids.extend(sorted(ids))
        else:
            missing.append({"author": t.get("author"), "works": t.get("works")})
    return {"primary_required": True, "primary_target_mode": mode,
            "resolved_targets": resolved, "read_target_ids": sorted(set(read_ids)),
            "primary_satisfied": satisfied, "missing_targets": missing}
