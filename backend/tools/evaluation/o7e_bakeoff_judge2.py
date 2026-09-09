# -*- coding: utf-8 -*-
"""O7-E Bakeoff V2 §B: canonical academic judge——零自写合同。

唯一 judge 合同 = O7-A 冻结件（JUDGE_SYSTEM_PROMPT/build_judge_input/
render_judge_prompt/validate_verdict/DIMENSIONS/FATAL_FLAGS）。
O7-E 只固定 invocation（glm-4.6/temp0/disabled/json/k3）与 manifest applicability。
"""
import json
import os
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


def _materialize_read_chapters(r, max_chapters=6):
    """PF-RP3A §B EVIDENCE REPLAY: 把 run facts.read_chapters 记录的当时已读章节
    从本地书库机械物化（⊆ RUN_FACTS_READ_CHAPTERS; 零新增检索/零网络）。"""
    facts = (r.get("evidence_digest") or {}).get("facts") or {}
    keys = facts.get("read_chapters") or []
    out = {}
    for key in keys[:max_chapters]:
        try:
            book_id, idx = str(key).rsplit("#", 1)
            path = os.path.join(ROOT, "backend", "data", "book_chapters",
                                book_id, f"{int(idx)}.json")
            d = json.load(open(path, encoding="utf-8"))
            content = d.get("content") or ""
            if isinstance(content, list):
                # 分章标准: content 为块列表（str 或 {text/content} 块）
                parts = []
                for b in content:
                    if isinstance(b, str):
                        parts.append(b)
                    elif isinstance(b, dict):
                        parts.append(str(b.get("value") or b.get("text")
                                         or b.get("content") or ""))
                content = "\n".join(x for x in parts if x)
            out[key] = content
        except Exception:
            continue
    return out


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


def _replay_windows(r, max_windows=12):
    """答案中每个 verbatim claim → 已读章节里的 source window（机械, 无 validator 判断）。"""
    import quote_bound as QB
    ans = r.get("answer", "")
    texts = _materialize_read_chapters(r)
    if not texts:
        return []
    windows = []
    for q in QB.extract_quotes(ans)[:max_windows]:
        for key, text in texts.items():
            w = _source_window(text, q["text"], max_window=500)
            if w:
                windows.append({"chapter_key": key,
                                "source_window": w,
                                "for_answer_claim": q["text"][:80]})
                break
    return windows


def _judge_evidence_parts(r):
    """PF-RP2 §0: 拆分 canonical judge 的四类正式字段。
    PRIMARY_TEXT_EVIDENCE 只含既有 run 的真实 source text（used_evidence primary
    条目）; 答案侧引文是 answer_quote 映射, 不冒充 source text; secondary 与
    access_levels 走 build_judge_input 的独立正式字段; 缺的数据保持空。"""
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
    access_levels = []   # 本 run 未记录 access 状态——保持空, 不编造
    return primary_ev, secondary, access_levels


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
        replay = _replay_windows(r)
        if replay:
            primary_ev = primary_ev + [
                {"source": "evidence_replay_read_chapters", "entries": replay}]
        # PF-RP3A §A: manifest applicability 作为预注册 truth 进入 judge 输入
        manifest_applic = {d.lower(): a for d, a in
                           (m.get("applicability") or {}).items()}
        inp = O7A.build_judge_input(
            user_question=m["question"], task_category=m["task_category"],
            answer=r.get("answer", ""), agent_identity=m["agent_identity"],
            evidence_digest=json.dumps(
                {k: v for k, v in (r.get("evidence_digest") or {}).items()
                 if k != "facts"}, ensure_ascii=False)[:2000],
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
                       "votes_archive": votes_archive})
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
    evaluation_invalid = bool(missing_required) or missing > 0
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
