# -*- coding: utf-8 -*-
"""O7-E RP2 RCA-1 §1-3: Repair Issue Bundle——局部修复的机械上下文构造。

核心变化: 「答案里有这么一句有问题」→「candidate SHA=X 的字符 [start:end] 就是
vi_N 的修改对象」。anchor 全部机械生成（citation regex / quote_bound 引文提取
char_start/char_end）; evidence packet issue-complete（每个可解析 issue 必得
其 linked evidence——LINKED_EVIDENCE_STARVATION=0）。

只做机械上下文构造; 零语义路由; 零 LLM。
"""
import hashlib
import json
import re

import quote_bound as QB

# §3 新合同
MAX_EVIDENCE_PER_ISSUE = 2
MAX_CONTEXT_PER_EVIDENCE = 400
MAX_TOTAL_REPAIR_CONTEXT_CHARS = 6000

# §4 分流白名单: 仅这些 deterministic issue code 走 LOCAL_PATCH
LOCAL_PATCH_CODES = {"UNVERIFIED_CITATION", "UNSUPPORTED_EXACT_QUOTE",
                     "NEAR_QUOTE_NOT_MARKED", "STITCHED_QUOTE"}


def _sha(s):
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def _span_sha(candidate, start, end):
    return _sha(candidate[start:end])[:16]


def _resolve_evidence(evidence_ref, raw_tool_log):
    """复用 engine 的双命名空间 resolver 语义（本地轻量实现, 避免循环 import）。"""
    import evidence_contract as EC
    ref = (evidence_ref or "").strip()
    if re.fullmatch(r"ev_\d+", ref):
        for c in EC._extract_candidates(raw_tool_log or []):
            if c.get("evidence_id") == ref:
                return {"kind": "citation", "payload": c}
        return "citation", None
    if ref.startswith(("qb_read_", "qb_snip_", "qb_corp_")):
        for s in QB.evidence_spans(raw_tool_log or []):
            if s.get("evidence_id") == ref:
                return "quote", s
        return "quote", None
    return "unknown", None


def _best_unit(locator, units, max_context=MAX_CONTEXT_PER_EVIDENCE):
    qn = QB.norm_q(locator or "")
    if not qn:
        return None, 0.0
    qsh = QB._shingles(qn)
    best, best_score = None, 0.0
    for u in units or []:
        ush = QB._shingles(QB.norm_q(u))
        score = len(qsh & ush) / max(len(qsh), 1)
        if score > best_score:
            best, best_score = u, score
    return (best[:max_context] if best else None), round(best_score, 2)


def _citation_anchor(candidate, locator):
    """formal citation 【《书》·章】regex 直接定位。"""
    if not locator:
        return None
    idx = candidate.find(locator)
    if idx < 0:
        # 容错: locator 可能被截断——取前 24 字符再找
        idx = candidate.find(locator[:24])
    if idx < 0:
        return None
    return {"start": idx, "end": idx + len(locator)}


def _quote_anchor(candidate, locator, exclude_spans=None):
    """quote issue: 复用 extract_quotes 的 char 锚——按 locator 文本匹配对应引文。

    exclude_spans: 已被其他 bundle 占用的 (start,end)——多引文场景防止同一引文
    被重复锚定（A3: duplicate preview 不得静默选错/重复 span）。"""
    exclude_spans = exclude_spans or set()
    loc = (locator or "").strip().strip("「」> ").strip()
    if not loc:
        return None
    best = None
    for q in QB.extract_quotes(candidate):
        qs, qe = q.get("char_start"), q.get("char_end")
        if qs is None:
            idx = candidate.find(q["text"][:60])
            if idx < 0:
                continue
            qs, qe = idx, idx + len(q["text"])
        if any(not (qe <= s or qs >= e) for s, e in exclude_spans):
            continue
        # 相关度: locator 与引文文本的重叠
        qn, ln = QB.norm_q(q["text"]), QB.norm_q(loc)
        rel = (len(QB._shingles(ln) & QB._shingles(qn)) /
               max(len(QB._shingles(ln)), 1))
        if best is None or rel > best[0]:
            best = (rel, qs, qe)
    if best and best[0] >= 0.15:
        return {"start": best[1], "end": best[2]}
    # 回退: 文本查找（排除已占用）
    idx = candidate.find(loc[:40])
    while idx >= 0 and any(not (idx + len(loc) <= s or idx >= e)
                           for s, e in exclude_spans):
        idx = candidate.find(loc[:40], idx + 1)
    return {"start": idx, "end": idx + len(loc)} if idx >= 0 else None


def build_repair_issue_bundles(candidate, validation_result, raw_tool_log):
    """validator issues → RepairIssueBundle 列表（机械, 确定性）。

    每个 bundle: {issue_id, code, anchor{start,end,surface_sha256,surface_preview},
    evidence_ref, source{book,chapter,exact_context}}
    """
    issues = validation_result.as_dict().get("issues", [])
    bundles = []
    total_ctx = 0
    _used_spans = set()
    for n, i in enumerate(issues, 1):
        code = (i or {}).get("code")
        locator = (i or {}).get("locator") or ""
        ref = (i or {}).get("evidence_ref")
        anchor = None
        if code == "UNVERIFIED_CITATION":
            anchor = _citation_anchor(candidate, locator)
        elif code in ("UNSUPPORTED_EXACT_QUOTE", "NEAR_QUOTE_NOT_MARKED",
                      "STITCHED_QUOTE"):
            anchor = _quote_anchor(candidate, locator,
                                   exclude_spans=_used_spans)
        if anchor:
            _used_spans.add((anchor["start"], anchor["end"]))
        bundle = {
            "issue_id": f"vi_{n}", "code": code,
            "anchor": ({"start": anchor["start"], "end": anchor["end"],
                        "surface_sha256": _span_sha(candidate, anchor["start"],
                                                    anchor["end"]),
                        "surface_preview": candidate[anchor["start"]:anchor["end"]][:60]}
                       if anchor else None),
            "evidence_ref": ref,
            "source": None}
        # evidence: issue-complete（可解析 ref 必给; 上限内给满）;
        # MEMORY_ONLY 无 ref → best-effort 给最高重叠 span（仍机械, 供 COPY_SLICE/转述参考）
        if not ref and code in ("UNSUPPORTED_EXACT_QUOTE", "STITCHED_QUOTE",
                                "NEAR_QUOTE_NOT_MARKED") and raw_tool_log:
            _ctx, _ov = _best_unit(locator,
                                    [u for s in QB.evidence_spans(raw_tool_log)
                                     for u in s.get("units") or []])
            if _ctx and _ov >= 0.2 and total_ctx + len(_ctx) <= MAX_TOTAL_REPAIR_CONTEXT_CHARS:
                bundle["source"] = {"book": None, "chapter": None,
                                    "exact_context": _ctx,
                                    "shingle_overlap": _ov, "best_effort": True}
                total_ctx += len(_ctx)
        if ref:
            kind, payload = _resolve_evidence(ref, raw_tool_log)
            if payload is not None and kind == "quote":
                ctx, overlap = _best_unit(locator, payload.get("units"))
                if ctx and total_ctx + len(ctx) <= MAX_TOTAL_REPAIR_CONTEXT_CHARS:
                    bundle["source"] = {"book": payload.get("book"),
                                        "chapter": payload.get("chapter"),
                                        "exact_context": ctx,
                                        "shingle_overlap": overlap,
                                        "source_char_length": len(payload.get("units") and
                                                                  "".join(payload["units"]) or "")}
                    total_ctx += len(ctx)
            elif payload is not None and kind == "citation":
                snip = str(payload.get("snippet") or "")[:MAX_CONTEXT_PER_EVIDENCE]
                if snip and total_ctx + len(snip) <= MAX_TOTAL_REPAIR_CONTEXT_CHARS:
                    bundle["source"] = {"book": payload.get("book"),
                                        "chapter": payload.get("chapter"),
                                        "exact_context": snip}
                    total_ctx += len(snip)
        bundles.append(bundle)
    return bundles


def render_patch_prompt(candidate_sha, bundles):
    """Main Agent 的 LOCAL_PATCH 输出合同 prompt（机械模板, 零语义指令）。"""
    return ("The final candidate (sha256=" + candidate_sha + ") failed deterministic "
            "validation on LOCAL issues. Instead of rewriting the whole answer, output "
            "ONLY a JSON patch object:\n"
            '{"candidate_sha256": "' + candidate_sha + '", "patches": ['
            '{"issue_id": "vi_N", "anchor_sha256": "...", "action": "REPLACE_TEXT", '
            '"replacement_text": "..."} or '
            '{"issue_id": "vi_N", "anchor_sha256": "...", "action": "COPY_EVIDENCE_SLICE", '
            '"evidence_ref": "...", "source_start": 42, "source_end": 91} ...]}\n'
            "Rules: every vi_N listed below must be covered by exactly one patch. "
            "For verbatim quotes prefer COPY_EVIDENCE_SLICE copying a continuous "
            "substring of the issue's source.exact_context (source_start/end are "
            "character offsets into that exact_context). REPLACE_TEXT text is your own "
            "prose (paraphrase, citation fix). Do not output anything besides the JSON.\n\n"
            "ISSUES:\n" + json.dumps(bundles, ensure_ascii=False)[:MAX_TOTAL_REPAIR_CONTEXT_CHARS])


def apply_main_agent_patches(candidate, patch_json, bundles):
    """§6-7: 机械 Patch Applier。

    验证 candidate/anchor SHA、issue_id、非重叠、evidence slice 归属; 倒序替换。
    零 runtime 文本生成（RUNTIME_GENERATED_PROSE_CHARS=0）;
    非目标正文 byte-preserved（NON_TARGET_TEXT_CHANGED_CHARS=0）。
    返回 (new_candidate | None, errors)。"""
    try:
        p = json.loads(patch_json)
    except Exception:
        return None, ["PATCH_PROTOCOL_ERROR: invalid JSON"]
    errs = []
    if p.get("candidate_sha256") != _sha(candidate):
        return None, ["PATCH_PROTOCOL_ERROR: candidate_sha mismatch"]
    covered = set()
    spans = []
    for pt in p.get("patches") or []:
        iid = pt.get("issue_id")
        bundle = next((b for b in bundles if b["issue_id"] == iid), None)
        if bundle is None:
            errs.append(f"PATCH_PROTOCOL_ERROR: unknown issue_id {iid}")
            continue
        if iid in covered:
            errs.append(f"PATCH_PROTOCOL_ERROR: duplicate patch {iid}")
            continue
        covered.add(iid)
        a = bundle.get("anchor")
        if not a:
            errs.append(f"PATCH_PROTOCOL_ERROR: {iid} has no anchor")
            continue
        if pt.get("anchor_sha256") != a["surface_sha256"]:
            errs.append(f"PATCH_PROTOCOL_ERROR: {iid} anchor stale")
            continue
        action = pt.get("action")
        if action == "REPLACE_TEXT":
            rep = pt.get("replacement_text")
            if not isinstance(rep, str) or not rep.strip():
                errs.append(f"PATCH_PROTOCOL_ERROR: {iid} empty replacement")
                continue
            text = rep
        elif action == "COPY_EVIDENCE_SLICE":
            src = bundle.get("source") or {}
            ctx = src.get("exact_context") or ""
            s, e = pt.get("source_start"), pt.get("source_end")
            if not (isinstance(s, int) and isinstance(e, int) and 0 <= s < e <= len(ctx)):
                errs.append(f"PATCH_PROTOCOL_ERROR: {iid} invalid evidence slice")
                continue
            if pt.get("evidence_ref") != bundle.get("evidence_ref"):
                errs.append(f"PATCH_PROTOCOL_ERROR: {iid} evidence_ref mismatch")
                continue
            text = ctx[s:e]
        else:
            errs.append(f"PATCH_PROTOCOL_ERROR: {iid} unknown action {action!r}")
            continue
        spans.append((a["start"], a["end"], text, iid))
    # 未覆盖的 LOCAL issue = 协议错误
    for b in bundles:
        if b["issue_id"] not in covered:
            errs.append(f"PATCH_PROTOCOL_ERROR: {b['issue_id']} not patched")
    if errs:
        return None, errs
    # 重叠检测 + 倒序应用
    spans.sort(key=lambda t: -t[0])
    last_start = None
    for s, e, _, iid in spans:
        if last_start is not None and e > last_start:
            return None, [f"PATCH_PROTOCOL_ERROR: overlapping patches at {iid}"]
        last_start = s
    new = candidate
    for s, e, text, _ in spans:
        new = new[:s] + text + new[e:]
    return new, []


def non_target_changed_chars(original, patched, spans):
    """§7 验证: anchor 范围外零字节变化。"""
    if patched is None:
        return -1
    # 应用后的 span 区间长度变化——用对齐近似: 逐段比较非目标前缀/后缀
    # 简化实现: 验证 patched 以原前缀开头、以原后缀结尾（首个 span 前/最后 span 后）
    if not spans:
        return 0 if original == patched else -1
    spans_sorted = sorted(spans)
    pre_end = spans_sorted[0][0]
    post_start = spans_sorted[-1][1]
    if patched[:pre_end] != original[:pre_end]:
        return -1
    if patched[len(patched) - (len(original) - post_start):] != original[post_start:]:
        return -1
    return 0
