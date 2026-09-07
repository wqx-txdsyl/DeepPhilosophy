# -*- coding: utf-8 -*-
"""O7-E RP2 Closure H/I: canonical primary-truth mechanical evaluator（evaluation-only）。

生产 runtime 零 semantic router（§14）; 本模块只被 Final Gate/测试调用,
定义 PRIMARY_REQUIRED 的真正含义:
  满足 = target 作者/作品的实际 primary-body read（get_chapter 全文或等价）
  不满足 = 仅 search snippet / 二手评论书
ALL 语义 = 每个 target 都需实际 primary read（比较题双边）。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def primary_reads(tool_log):
    """已取得的 primary-body reads: {book_id}（get_chapter 全文类）。"""
    reads = set()
    for t in tool_log or []:
        if (t.get("name") or "") != "get_chapter":
            continue
        rf = t.get("result_full")
        if isinstance(rf, dict) and rf.get("text") and not rf.get("error"):
            bid = (t.get("args") or {}).get("book_id") or rf.get("book_id")
            if bid:
                reads.add(bid)
    return reads


def primary_satisfied(case, tool_log):
    """None=该 case 无 primary 维度; True/False=按 mode ANY/ALL 判定。"""
    targets = case.get("primary_targets") or []
    if not targets:
        return None
    mode = case.get("primary_target_mode", "ANY")
    reads = primary_reads(tool_log)
    # 解析 resolution manifest 的扩展 book_ids
    man_path = os.path.join(ROOT, "docs/evidence",
                            "PHIAGENT_O7E_RP2_PRIMARY_TARGET_RESOLUTION.json")
    extra = {}
    if os.path.exists(man_path):
        for x in json.load(open(man_path, encoding="utf-8")):
            if isinstance(x, dict) and x.get("resolved_book_ids"):
                extra[(x.get("case_id"), x.get("author"), x.get("work"))] = x["resolved_book_ids"]
    hits = 0
    for t in targets:
        ids = set(t.get("book_ids") or [])
        ids |= set(extra.get((case.get("case_id"), t.get("author"),
                              (t.get("works") or [""])[0]), []))
        if ids & reads:
            hits += 1
    if mode == "ALL":
        return hits == len(targets)
    return hits >= 1


def check_case(case, run):
    """Final Gate 单案例 primary 检查（Closure-2 §3: 消费 runner 已保存的
    evidence_digest.read_chapters 机械事实——book_id#chapter_idx 列表）。"""
    targets = case.get("primary_targets") or []
    if not targets:
        return {"primary_required": False}
    ev = run.get("evidence_digest") or {}
    reads_raw = []
    facts = ev.get("facts") or {}
    if isinstance(facts, dict):
        rc = facts.get("read_chapters") or []
        reads_raw = [str(x) for x in rc]
    read_pairs = set()
    for r in reads_raw:
        b, _, c = r.partition("#")
        read_pairs.add((b, c))
    read_book_ids = {b for b, _ in read_pairs}
    mode = case.get("primary_target_mode", "ANY")
    extra = {}
    man_subwork = []
    man_path = os.path.join(ROOT, "docs/evidence",
                            "PHIAGENT_O7E_RP2_PRIMARY_TARGET_RESOLUTION.json")
    if os.path.exists(man_path):
        for x in json.load(open(man_path, encoding="utf-8")):
            if not isinstance(x, dict):
                continue
            if x.get("resolved_book_ids"):
                extra[(x.get("case_id"), x.get("author"), x.get("work"))] = x["resolved_book_ids"]
            if x.get("identity_scope") == "BOOK_SUBWORK":
                man_subwork.append(x)
    # RP-DEC §7-9: SUBWORK 合集目标需要 book_id + 目标章节索引命中
    subwork_idx = {}
    for x in man_subwork:
        subwork_idx[(x.get("case_id"), x.get("work"))] = x
    resolved, read_ids, missing = [], [], []
    for t in targets:
        work = (t.get("works") or [""])[0]
        ids = set(t.get("book_ids") or [])
        ids |= set(extra.get((case.get("case_id"), t.get("author"), work), []))
        sw = subwork_idx.get((case.get("case_id"), work))
        if sw:
            chaps = set(sw.get("resolved_chapter_indices") or [])
            hit = sorted({b for b, c in read_pairs
                          if b == sw.get("resolved_book_id")
                          and (c.lstrip("-").isdigit() and int(c) in chaps)})
        else:
            hit = sorted(ids & read_book_ids)
        resolved.append({"author": t.get("author"),
                         "works": t.get("works"), "book_ids": sorted(ids),
                         "identity_scope": "BOOK_SUBWORK" if sw else "BOOK"})
        if hit:
            read_ids.extend(hit)
        else:
            missing.append({"author": t.get("author"),
                            "works": t.get("works")})
    satisfied = (len(missing) == 0) if mode == "ALL" else (len(read_ids) >= 1)
    return {"primary_required": True, "primary_target_mode": mode,
            "resolved_targets": resolved, "read_target_ids": sorted(set(read_ids)),
            "primary_satisfied": satisfied, "missing_targets": missing}
