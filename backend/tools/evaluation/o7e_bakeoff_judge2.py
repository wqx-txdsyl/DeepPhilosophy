# -*- coding: utf-8 -*-
"""O7-E Bakeoff V2 §B: canonical academic judge——零自写合同。

唯一 judge 合同 = O7-A 冻结件（JUDGE_SYSTEM_PROMPT/build_judge_input/
render_judge_prompt/validate_verdict/DIMENSIONS/FATAL_FLAGS）。
O7-E 只固定 invocation（glm-4.6/temp0/disabled/json/k3）与 manifest applicability。
"""
import json
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, os.path.join(ROOT, "backend", "tools", "evaluation"))

import o7_scholarly_judge as O7A   # canonical judge constitution（冻结）
import quote_bound as QB

_key = None
for line in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
    if line.strip().startswith("ZHIPU_API_KEY="):
        _key = line.split("=", 1)[1].strip().strip('"').strip("'")


def _call(prompt):
    payload = {"model": "glm-4.6", "temperature": 0, "max_tokens": 4000,
               "thinking": {"type": "disabled"},
               "response_format": {"type": "json_object"},
               "messages": [{"role": "system", "content": O7A.JUDGE_SYSTEM_PROMPT},
                            {"role": "user", "content": prompt}]}
    req = urllib.request.Request(O7A.JUDGE_BASE_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + (_key or "")})
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"] or ""


def _materialize_read_chapters(r, max_chapters=None):
    """PF-RP3A §B EVIDENCE REPLAY + PF-RP4B-R1: 把 run facts.read_chapters 记录的
    当时已读章节从本地书库机械物化（零新增检索/零网络/零 fuzzy）。

    支持 key: canonical "book_id#idx"; legacy "书名#idx" 只允许用同一次 run 已有
    evidence records（citations + used/candidate/retrieved_evidence）建立的
    (book, chapter_idx)→(book_id, idx) 唯一精确别名解析
    （RUN_EVIDENCE_EXACT_ALIAS）; 0 个 target → UNRESOLVED;
    >1 个不同 target → AMBIGUOUS_RUN_EVIDENCE_ALIAS;
    两者都记入 failed（调用方据此置 EVALUATION_INVALID, 不静默评分）。
    遍历全部 facts.read_chapters——无 silent cap（PF-RP4B-R1）。
    返回 (texts, resolution)。"""
    facts = (r.get("evidence_digest") or {}).get("facts") or {}
    keys = facts.get("read_chapters") or []
    out, failed, resolution = {}, [], {}
    # PF-RP4B-R1: exact alias provenance pool = 同一 run 的四类机械记录
    alias = {}

    def _add_alias(entry):
        if (isinstance(entry, dict) and entry.get("book")
                and isinstance(entry.get("chapter_idx"), int)
                and entry.get("book_id")):
            alias.setdefault((entry["book"], entry["chapter_idx"]),
                             set()).add((entry["book_id"], entry["chapter_idx"]))

    for c in r.get("citations") or []:
        _add_alias(c)                                    # ALIAS_SOURCE_CITATIONS
    ev = r.get("evidence_digest") or {}
    for pool_key in ("used_evidence", "candidate_evidence", "retrieved_evidence"):
        for e in ev.get(pool_key) or []:
            _add_alias(e)                                # USED/CANDIDATE/RETRIEVED
    for key in keys:                                     # 无 silent cap
        k = str(key)
        resolved, mode = None, "UNRESOLVED"
        try:
            if "#" in k:
                left, idx_s = k.rsplit("#", 1)
                idx = int(idx_s)
                if _CH_ID_RE.fullmatch(left):
                    resolved, mode = (left, idx), "CANONICAL_ID"
                else:
                    matches = alias.get((left, idx))
                    if matches and len(matches) == 1:
                        resolved, mode = next(iter(matches)), "RUN_EVIDENCE_EXACT_ALIAS"
                    elif matches and len(matches) > 1:
                        mode = "AMBIGUOUS_RUN_EVIDENCE_ALIAS"
            elif k in alias and len(alias[k]) == 1:
                resolved, mode = next(iter(alias[k])), "RUN_EVIDENCE_EXACT_ALIAS"
            elif k in alias and len(alias[k]) > 1:
                mode = "AMBIGUOUS_RUN_EVIDENCE_ALIAS"
        except Exception:
            resolved = None
        if resolved is None:
            failed.append(key)
            resolution[k] = mode
            continue
        book_id, idx = resolved
        try:
            path = os.path.join(ROOT, "backend", "data", "book_chapters",
                                book_id, f"{idx}.json")
            d = json.load(open(path, encoding="utf-8"))
            content = d.get("content") or ""
            if isinstance(content, list):
                parts = []
                for b in content:
                    if isinstance(b, str):
                        parts.append(b)
                    elif isinstance(b, dict):
                        parts.append(str(b.get("value") or b.get("text")
                                         or b.get("content") or ""))
                content = "\n".join(x for x in parts if x)
            out[k] = content
            resolution[k] = mode
        except Exception:
            failed.append(key)
            resolution[k] = "UNRESOLVED"
    return out, {"resolution": resolution, "failed": failed}


_CH_ID_RE = re.compile(r"[0-9a-f]{8,}")


def _materialize_with_meta(r):
    texts, resolution = _materialize_read_chapters(r)
    meta = {"read_chapters_recorded": len((r.get("evidence_digest") or {})
                                          .get("facts", {}).get("read_chapters") or []),
            "read_chapters_materialized": len(texts),
            "read_chapters_materialize_failed": len(resolution["failed"]),
            "materialize_failed_keys": resolution["failed"],
            "resolution_modes": resolution["resolution"],
            "legacy_resolved": sum(1 for m in resolution["resolution"].values()
                                   if m == "RUN_EVIDENCE_EXACT_ALIAS")}
    return texts, meta


def _source_window(text, claim, max_window=500):
    """机械截取 claim 在章节原文中的最佳对应 window（≤500 字符）——
    用 QuoteBound 归一 shingle 选区, 不下 EXACT/NEAR 结论。"""
    qn = QB.norm_q(claim)
    if not qn or not text:
        return None
    nt = QB.norm_q(text)
    step, wlen = 300, 500
    best, best_ov = None, 0.0
    qsh = QB._shingles(qn)
    for i in range(0, max(len(nt) - wlen, 1), step):
        w = nt[i:i + wlen]
        ov = len(QB._shingles(w) & qsh) / max(len(qsh), 1)
        if ov > best_ov:
            best, best_ov = i, ov
    if best is None or best_ov < 0.05:
        return None
    # 归一坐标近似映射回原文: 按比例定位
    ratio = best / max(len(nt) - wlen, 1)
    center = int(ratio * max(len(text) - wlen, 1))
    return text[max(0, center - 0):center + wlen]


def _compact_digest(r):
    """PF-RP4A §A: 结构化 compact digest——不再对整份 JSON 做盲目前缀截断。"""
    ev = r.get("evidence_digest") or {}
    return {
        "retrieved_count": ev.get("retrieved_count"),
        "used_count": ev.get("used_count"),
        "used_evidence": [{"evidence_id": e.get("evidence_id"),
                           "book": e.get("book"), "chapter": e.get("chapter"),
                           "source_type": e.get("source_type")}
                          for e in (ev.get("used_evidence") or [])
                          if isinstance(e, dict)][:12],
        "scholarly_facts": ev.get("scholarly_facts") or {},
        "scholarly_access": ev.get("scholarly_access") or {},
    }


def _judge_evidence_parts(r):
    """PF-RP2 §0 / PF-RP3B §E: 拆分 canonical judge 的四类正式字段。
    PRIMARY_TEXT_EVIDENCE 只含既有 run 的真实 source text（used_evidence primary
    条目 + evidence replay windows）; 答案侧引文是 answer_quote 映射, 不冒充
    source text; secondary（web + scholarly records/passage）与 access_levels 走
    build_judge_input 的独立正式字段; 缺的数据保持空, 不编造。"""
    ev = r.get("evidence_digest") or {}
    facts = ev.get("facts") or {}
    used = [e for e in (ev.get("used_evidence") or []) if isinstance(e, dict)]
    primary = [{"evidence_id": e.get("evidence_id"),
                "source_type": e.get("source_type"),
                "book": e.get("book"), "chapter": e.get("chapter"),
                "source_text": ((e.get("text") or e.get("snippet") or "")[:400])
                } for e in used
               if e.get("source_type") in ("primary_read", "primary", "snippet")
               and (e.get("text") or e.get("snippet"))][:10]
    qb = [e for e in (r.get("quote_bound") or [])
          if e.get("verification_state") in ("VERIFIED_EXACT", "VERIFIED_NEAR")]
    answer_quotes = [{"answer_quote": e.get("preview"),
                      "evidence_id": e.get("source_evidence_id"),
                      "state": e.get("verification_state")} for e in qb[:12]]
    primary_ev = [
        {"source": "primary_evidence_from_existing_run",
         "entries": primary},
        {"source": "answer_quote_to_evidence_mapping",
         "entries": answer_quotes},
        {"source": "read_chapters", "chapters": facts.get("read_chapters")},
    ]
    secondary = [{"book": e.get("book"), "chapter": e.get("chapter"),
                  "source_type": e.get("source_type"),
                  "evidence_id": e.get("evidence_id")}
                 for e in used if e.get("source_type") == "secondary"][:6]
    # PF-RP3B §E: scholarly evidence 只来自 run artifact——禁止事后 registry 查询
    schol = r.get("scholarly_provenance") or {}
    ev_by_id = {e.get("source_record_id"): e
                for e in (schol.get("scholarly_evidence") or [])}
    sec_records = []
    for rec in schol.get("scholarly_records") or []:
        entry = dict(rec)
        e = ev_by_id.get(rec.get("source_record_id"))
        if e:
            if e.get("abstract_text"):
                entry["abstract_text"] = e["abstract_text"][:1200]
            if e.get("evidence_passages"):
                entry["evidence_passages"] = e["evidence_passages"][:5]
            entry["access_level_after"] = e.get("access_level_after")
        sec_records.append(entry)
    access_levels = [{"source_record_id": k, "access_level": lvl}
                     for k, lvl in (schol.get("SCHOLARLY_ACCESS_LEVELS")
                                    or {}).items()]
    return primary_ev, secondary + sec_records, access_levels


def _best_window(text, claim, wlen=500):
    """章节原文中与 claim 归一 shingle 重叠最高的窗口起点（保留原文坐标）。"""
    qsh = QB._shingles(QB.norm_q(claim))
    if not qsh or not text:
        return None, 0.0
    best_i, best_ov = None, 0.0
    n = len(text)
    if n <= wlen:
        ov = len(QB._shingles(QB.norm_q(text)) & qsh) / max(len(qsh), 1)
        return (0, ov) if ov >= 0.05 else (None, 0.0)
    for i in list(range(0, n - wlen + 1, 300)) + [max(n - wlen, 0)]:
        ov = len(QB._shingles(QB.norm_q(text[i:i + wlen])) & qsh) / max(len(qsh), 1)
        if ov > best_ov:
            best_i, best_ov = i, ov
    return (best_i, best_ov) if best_i is not None else (None, 0.0)


def _replay_windows(r, max_windows=24, max_window_chars=500):
    """PF-RP4A §A: 全量候选机械 replay 选择——绝不做 positional 截断。

    候选 = 答案全部 quote-like spans + evidence contract 中 substantial claim
    texts（有 evidence_ids 或 TEXTUAL_CLAIM）; 对每个候选在全部已物化已读章节
    上算确定性 shingle overlap → 排序 → 同章节近区去重 → bounded top-K。
    只提供 source text, 不携带 validator 的 EXACT/NEAR/MEMORY_ONLY 结论。"""
    ev = r.get("evidence_digest") or {}
    facts = ev.get("facts") or {}
    recorded = facts.get("read_chapters") or []
    texts, mat_meta = _materialize_read_chapters(r)
    failed = mat_meta["failed"]
    ans = r.get("answer", "")
    candidates = [q.get("text") or "" for q in QB.extract_quotes(ans)]
    # PF-RP4A §A: textual claim 不一定带外层引号（H13 实况——整句转述+内部
    # scare quotes）→ 答案句级候选作为机械超集; 归一文本去重
    import re as _re
    seen_norm = set()
    sentences = [s.strip() for s in _re.split(r"[。！？\n]", ans) if s.strip()]
    for s in sentences:
        if len(QB.norm_q(s)) >= 12:
            n = QB.norm_q(s)
            if n not in seen_norm:
                seen_norm.add(n)
                candidates.append(s)
    for c in (ev.get("claims") or []):
        if isinstance(c, dict) and (c.get("evidence_ids")
                                    or c.get("role") == "TEXTUAL_CLAIM"):
            t = (c.get("text") or "").strip()
            if t and len(QB.norm_q(t)) >= 12:
                n = QB.norm_q(t)
                if n not in seen_norm:
                    seen_norm.add(n)
                    candidates.append(t)
    candidates = [c.strip() for c in candidates if c.strip()]
    scored = []
    for t in candidates:
        best = None
        for key in sorted(texts):
            i, ov = _best_window(texts[key], t, max_window_chars)
            if i is not None and ov >= 0.05 and (best is None or ov > best[0]):
                best = (ov, key, i)
        if best is not None:
            scored.append((best[0], best[1], best[2], t))
    scored.sort(key=lambda x: -x[0])
    matched = len(scored)
    windows, seen_regions = [], []
    for ov, key, i, t in scored:
        if any(k == key and abs(i - j) < 250 for k, j in seen_regions):
            continue
        if len(windows) >= max_windows:
            break
        seen_regions.append((key, i))
        windows.append({"chapter_key": key,
                        "source_window": texts[key][i:i + max_window_chars],
                        "for_answer_claim": t[:80],
                        "overlap": round(ov, 2)})
    meta = {"read_chapters_recorded": len(recorded),
            "read_chapters_materialized": len(texts),
            "read_chapters_materialize_failed": len(failed),
            "materialize_failed_keys": failed,
            "resolution_modes": mat_meta["resolution"],
            "legacy_resolved": sum(1 for m in mat_meta["resolution"].values()
                                   if m == "RUN_EVIDENCE_EXACT_ALIAS"),
            "primary_replay_candidates": len(candidates),
            "primary_replay_matched": matched,
            "primary_replay_windows": len(windows),
            "primary_replay_coverage_rate": round(
                matched / max(len(candidates), 1), 3),
            "new_primary_source_ids": 0}
    return windows, meta


def judge_candidate(mid, runs_path=None, out_tag=None):
    runs = json.load(open(runs_path or os.path.join(
        ROOT, "backend/tools/_tmp", f"o7e_bakeoff_B_{mid.replace('.','_')}.json"),
        encoding="utf-8"))
    man = {m["case_id"]: m for m in json.load(open(os.path.join(
        ROOT, "docs/evidence/PHIAGENT_O7E_BAKEOFF_EVALUATION_MANIFEST.json"),
        encoding="utf-8"))}
    tag = out_tag or f"o7e_bakeoff_judge2_{mid.replace('.','_')}"
    out_path = os.path.join(ROOT, "backend/tools/_tmp", f"{tag}.json")
    judged = []
    if os.path.exists(out_path):
        judged = json.load(open(out_path, encoding="utf-8"))
    done = {j["case_id"] for j in judged}
    for r in runs:
        cid = r["case_id"]
        if cid in done or not r.get("delivery", {}).get("published"):
            continue
        m = man[cid]
        primary_ev, secondary, access_levels = _judge_evidence_parts(r)
        # PF-RP3A §B EVIDENCE REPLAY: 已读章节机械物化 → verbatim claim 的
        # source window（≤500 字符）——judge 与 validator 看同一证据事实,
        # 但不含 validator 的 EXACT/NEAR/MEMORY_ONLY 结论
        replay, replay_meta = _replay_windows(r)
        if replay:
            primary_ev = primary_ev + [
                {"source": "evidence_replay_read_chapters", "entries": replay}]
        # PF-RP3A §A: manifest applicability 作为预注册 truth 进入 judge 输入
        manifest_applic = {d.lower(): a for d, a in
                           (m.get("applicability") or {}).items()}
        inp = O7A.build_judge_input(
            user_question=m["question"], task_category=m["task_category"],
            answer=r.get("answer", ""), agent_identity=m["agent_identity"],
            # PF-RP4A §A: 结构化 compact digest 取代整份 JSON 的盲目前缀截断
            evidence_digest=json.dumps(_compact_digest(r), ensure_ascii=False),
            primary_text_evidence=primary_ev,
            bibliographic_records=(r.get("citations") or [])[:8],
            secondary_source_records=secondary,
            access_levels=access_levels,
            dimension_applicability=manifest_applic)
        prompt = O7A.render_judge_prompt(inp)
        votes = []
        for k in range(3):
            for attempt in range(3):
                try:
                    votes.append(json.loads(_call(prompt)))
                    break
                except Exception:
                    time.sleep(2 * (attempt + 1))
            else:
                votes.append(None)
        # PF-RP3A §A: vote 级机械校验——applicability 必须等于 manifest 预注册;
        # REQUIRED 维必须给数值分, 否则该票 invalid（不静默采信 judge 自判）
        valid, mismatch_votes, votes_archive = [], 0, []
        for vi, v in enumerate(votes):
            if not v:
                votes_archive.append({"vote_index": vi, "valid": False,
                                      "reason": "vote_unparseable"})
                continue
            base_errs = O7A.validate_verdict(v)
            vdims = v.get("dimensions", {}) or {}
            bad = list(base_errs)
            for dim, applic in manifest_applic.items():
                vd = vdims.get(dim) or {}
                if (vd.get("applicability") or applic) != applic:
                    bad.append(f"{dim}: applicability {vd.get('applicability')!r} "
                               f"!= manifest {applic!r}")
                if applic == "REQUIRED" and not isinstance(
                        vd.get("score"), (int, float)):
                    bad.append(f"{dim}: REQUIRED requires numeric score")
            votes_archive.append({
                "vote_index": vi, "valid": not bad, "reasons": bad[:6],
                "dimensions": {d: {"applicability": (vd or {}).get("applicability"),
                                    "score": (vd or {}).get("score"),
                                    "rationale": (vd or {}).get("rationale"),
                                    "supporting_spans": (vd or {}).get("supporting_spans"),
                                    "missing_requirements": (vd or {}).get("missing_requirements")}
                               for d, vd in vdims.items()},
                "fatal_flags": {f: {"value": ((fd or {}).get("value")),
                                     "offending_spans": (fd or {}).get("offending_spans"),
                                     "reason": (fd or {}).get("reason"),
                                     "evidence_refs": (fd or {}).get("evidence_refs"),
                                     "confidence": (fd or {}).get("confidence")}
                                for f, fd in (v.get("fatal_flags") or {}).items()},
                "overall_scholarly_assessment": v.get("overall_scholarly_assessment"),
                "judge_confidence": v.get("judge_confidence")})
            if bad:
                mismatch_votes += 1
                continue
            valid.append(v)
        if not valid:
            judged.append({"case_id": cid, "error": "all judge votes invalid",
                           "votes_archive": votes_archive,
                           "applicability_mismatch_votes": mismatch_votes})
            json.dump(judged, open(out_path, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            continue
        # applicability 取 manifest 真值（judge 不猜）
        dims = {}
        required_missing = []
        for d in O7A.DIMENSIONS:
            scores = [((v.get("dimensions", {}).get(d) or {}).get("score"))
                      for v in valid]
            scores = [s for s in scores if isinstance(s, (int, float))]
            median = sorted(scores)[len(scores)//2] if scores else None
            applic = m["applicability"].get(d.upper(), "OPTIONAL")
            # D1: REQUIRED 维度无有效分 → 该 case 记 required_missing,
            # 不静默出分母、不当 0 分（聚合层置 EVALUATION_INVALID）
            if applic == "REQUIRED" and median is None:
                required_missing.append(d)
            dims[d] = {"median": median, "applicability": applic}
        fatal = set()
        for v in valid:
            for f in O7A.FATAL_FLAGS:
                if ((v.get("fatal_flags") or {}).get(f) or {}).get("value"):
                    fatal.add(f)
        fatal_vc = {}
        for v in valid:
            for f in O7A.FATAL_FLAGS:
                if ((v.get("fatal_flags") or {}).get(f) or {}).get("value"):
                    fatal_vc[f] = fatal_vc.get(f, 0) + 1
        judged.append({"case_id": cid, "dims": dims, "fatal": sorted(fatal),
                       "fatal_vote_counts": fatal_vc,
                       "applicability_mismatch_votes": mismatch_votes,
                       "required_missing": required_missing,
                       "votes_archive": votes_archive,
                       "replay_meta": replay_meta})
        json.dump(judged, open(out_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"  {cid}: " + " ".join(f"{d.split('_')[0]}={dims[d]['median']}"
                                      for d in dims) + f" fatal={sorted(fatal)}",
              flush=True)
    # aggregate（PF-RP2 §0: REQUIRED 与 applicable 分开记账）
    #   required_dims: 每维 REQUIRED 中位数均值（REQUIRED_*_MEAN 用, 不含 OPTIONAL）
    #   applicable_dims / applicable_mean: numeric REQUIRED + numeric OPTIONAL
    #   （NOT_APPLICABLE 与合法 OPTIONAL null 排除）
    required_scores = {}
    applicable_scores = {}
    fatal_total = set()
    fatal_counts = {f: 0 for f in O7A.FATAL_FLAGS}
    median_lt2 = 0
    missing_required = []
    expected = len([r for r in runs if r.get("delivery", {}).get("published")])
    valid = [j for j in judged if j.get("dims")]
    missing = expected - len(valid)
    for j in valid:
        if j.get("fatal"):
            fatal_total.update(j["fatal"])
            for f in j["fatal"]:
                if f in fatal_counts:
                    fatal_counts[f] += 1
        for d, dv in j.get("dims", {}).items():
            if dv["median"] is None:
                continue
            # PF-RP3: REQUIRED_MEDIAN_LT_2 = published case × manifest REQUIRED 维
            # 中 median < 2 的数量
            if dv["applicability"] == "REQUIRED" and dv["median"] < 2:
                median_lt2 += 1
            if dv["applicability"] == "REQUIRED":
                required_scores.setdefault(d, []).append(dv["median"])
                applicable_scores.setdefault(d, []).append(dv["median"])
            elif dv["applicability"] == "OPTIONAL":
                applicable_scores.setdefault(d, []).append(dv["median"])
        for d in (j.get("required_missing") or []):
            missing_required.append({"case_id": j["case_id"], "dimension": d})
    # error case（三票全废）也算 missing
    for j in judged:
        if j.get("error"):
            missing_required.append({"case_id": j["case_id"],
                                     "dimension": "ALL_JUDGE_VOTES_INVALID"})
    # PF-RP4B: 已读章节无法机械 replay → 不允许静默评分
    mat_failed_total = sum(len(j.get("replay_meta", {}).get("materialize_failed_keys") or [])
                           for j in judged if j.get("replay_meta"))
    evaluation_invalid = bool(missing_required) or missing > 0 or mat_failed_total > 0
    out = {"candidate": mid, "judged": len(valid),
           "JUDGE_CASES_EXPECTED": expected,
           "JUDGE_CASES_VALID": len(valid),
           "JUDGE_CASES_MISSING": max(missing, 0),
           "EVALUATION_INVALID": evaluation_invalid,
           "REQUIRED_DIMENSION_MISSING_SCORE": len(missing_required),
           "REQUIRED_DIMENSION_MEDIAN_LT_2": median_lt2,
           "FATAL_FLAG_COUNTS_BY_TYPE": fatal_counts,
           "missing_required": missing_required,
           "required_dims": {d: round(sum(xs) / len(xs), 3)
                             for d, xs in required_scores.items()},
           "applicable_dims": {d: round(sum(xs) / len(xs), 3)
                               for d, xs in applicable_scores.items()},
           "dims": {d: round(sum(xs) / len(xs), 3)
                    for d, xs in applicable_scores.items()},
           "applicable_mean": round(
               sum(x for xs in applicable_scores.values() for x in xs) /
               max(sum(len(xs) for xs in applicable_scores.values()), 1), 3),
           "fatal_flags": sorted(fatal_total)}
    json.dump(out, open(out_path.replace(".json", "_summary.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    judge_candidate(sys.argv[1])
