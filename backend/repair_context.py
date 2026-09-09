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
                return "citation", c
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


def _citation_anchor(candidate, locator, exclude_spans=None):
    """formal citation 【《书》·章】regex 直接定位（排除已占 span——H1 §3）。"""
    if not locator:
        return None
    exclude_spans = exclude_spans or set()

    def _free(i):
        return all(i + len(locator) <= s or i >= e for s, e in exclude_spans)

    idx = candidate.find(locator)
    while idx >= 0 and not _free(idx):
        idx = candidate.find(locator, idx + 1)
    if idx < 0:
        loc24 = locator[:24]
        idx = candidate.find(loc24)
        while idx >= 0 and not all(idx + len(loc24) <= s or idx >= e
                                    for s, e in exclude_spans):
            idx = candidate.find(loc24, idx + 1)
    if idx < 0:
        return None
    end = idx + len(locator)
    return {"start": idx, "end": end}


def _claim_content_span(candidate, q):
    """H1 §2: 从 quote claim 提取 content span（保留 wrapper/delimiters/leadin）。

    blockquote: claim=整块（含 > 行）, content=去 > 前缀后的正文
    leadin/quoted: claim=引号域, content=引号内文本
    返回 (claim_start, claim_end, content_start, content_end) 或 None。"""
    cs, ce = q.get("char_start"), q.get("char_end")
    if cs is None:
        return None
    raw = candidate[cs:ce]
    if q["kind"] == "blockquote":
        # 多行 blockquote 的 content 非单一 contiguous 正文（含 > 残留）→ 不安全
        lines = raw.split("\n")
        if len(lines) > 1:
            return None
        # 单行: "> 「text」" → content = 去掉 > 前缀后的「text」或 text
        m = re.match(r"^\s*>\s*(.*)$", raw)
        if not m:
            return None
        inner = m.group(1)
        c_start = cs + raw.index(inner) if inner else cs
        # 引号内: 找「或“ 对
        dm = re.match(r"^[「“](.*)[」”]$", inner)
        if dm:
            text = dm.group(1)
            t_off = c_start + inner.index(text)
            return (cs, ce, t_off, t_off + len(text))
        return (cs, ce, c_start, c_start + len(inner))
    # leadin/quoted: 引号内文本
    text = q["text"]
    idx = candidate.find(text, cs, ce + 200)
    if idx < 0:
        idx = cs
        # 兜底: claim 即 content
        return (cs, ce, cs, ce)
    return (cs, ce, idx, idx + len(text))


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
        claim = (best[1], best[2])
        # H1 §2: 拆 claim/content——COPY 只操作 content, wrapper 保留
        q_obj = next((q for q in QB.extract_quotes(candidate)
                      if q.get("char_start") == claim[0]), None)
        cc = _claim_content_span(candidate, q_obj) if q_obj else None
        if cc:
            return {"claim_start": cc[0], "claim_end": cc[1],
                    "content_start": cc[2], "content_end": cc[3],
                    "claim_sha256": _span_sha(candidate, cc[0], cc[1]),
                    "content_sha256": _span_sha(candidate, cc[2], cc[3]),
                    "start": cc[2], "end": cc[3]}   # 兼容字段=content
        return {"start": claim[0], "end": claim[1],
                "claim_start": claim[0], "claim_end": claim[1],
                "content_start": claim[0], "content_end": claim[1],
                "claim_sha256": _span_sha(candidate, claim[0], claim[1]),
                "content_sha256": _span_sha(candidate, claim[0], claim[1])}
    # 回退: 文本查找（排除已占用）
    idx = candidate.find(loc[:40])
    while idx >= 0 and any(not (idx + len(loc) <= s or idx >= e)
                           for s, e in exclude_spans):
        idx = candidate.find(loc[:40], idx + 1)
    if idx < 0:
        return None
    return {"start": idx, "end": idx + len(loc),
            "claim_start": idx, "claim_end": idx + len(loc),
            "content_start": idx, "content_end": idx + len(loc),
            "claim_sha256": _span_sha(candidate, idx, idx + len(loc)),
            "content_sha256": _span_sha(candidate, idx, idx + len(loc))}


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
            anchor = _citation_anchor(candidate, locator, _used_spans)
        elif code in ("UNSUPPORTED_EXACT_QUOTE", "NEAR_QUOTE_NOT_MARKED",
                      "STITCHED_QUOTE"):
            anchor = _quote_anchor(candidate, locator,
                                   exclude_spans=_used_spans)
        if anchor:
            _used_spans.add((anchor["claim_start"], anchor["claim_end"])
                            if "claim_start" in anchor
                            else (anchor["start"], anchor["end"]))
        if anchor and "claim_start" in anchor:
            anchor_out = {
                "claim_start": anchor["claim_start"], "claim_end": anchor["claim_end"],
                "content_start": anchor["content_start"],
                "content_end": anchor["content_end"],
                "claim_sha256": anchor["claim_sha256"],
                "content_sha256": anchor["content_sha256"],
                "surface_sha256": anchor["content_sha256"],   # patch 合同锚 = content
                "surface_preview": candidate[anchor["content_start"]:
                                            anchor["content_end"]][:60]}
        elif anchor:
            anchor_out = {
                "start": anchor["start"], "end": anchor["end"],
                "claim_start": anchor["start"], "claim_end": anchor["end"],
                "content_start": anchor["start"], "content_end": anchor["end"],
                "claim_sha256": _span_sha(candidate, anchor["start"], anchor["end"]),
                "content_sha256": _span_sha(candidate, anchor["start"], anchor["end"]),
                "surface_sha256": _span_sha(candidate, anchor["start"],
                                            anchor["end"]),
                "surface_preview": candidate[anchor["start"]:anchor["end"]][:60]}
        else:
            anchor_out = None
        bundle = {
            "issue_id": f"vi_{n}", "code": code,
            "anchor": anchor_out,
            "evidence_ref": ref,
            "source": None,
            # RCA-2 §metric: resolver 状态显式化——不再从 source is None 反推语义
            "evidence_resolution": "NOT_REQUIRED" if not ref else "UNRESOLVED"}
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
                    bundle["evidence_resolution"] = "RESOLVED"
                    total_ctx += len(ctx)
            elif payload is not None and kind == "citation":
                snip = str(payload.get("snippet") or "")[:MAX_CONTEXT_PER_EVIDENCE]
                if snip and total_ctx + len(snip) <= MAX_TOTAL_REPAIR_CONTEXT_CHARS:
                    bundle["source"] = {"book": payload.get("book"),
                                        "chapter": payload.get("chapter"),
                                        "exact_context": snip}
                    bundle["evidence_resolution"] = "RESOLVED"
                    total_ctx += len(snip)
        bundles.append(bundle)
    return bundles


def render_patch_prompt(candidate_sha, bundles):
    """Main Agent 的 LOCAL_PATCH 输出合同 prompt（机械模板, 零语义指令）。

    H1 §4: evidence context 预算——所有 issue identity（id/anchor sha/evidence_ref）
    永远保留; 超预算时逐条缩短 exact_context, 不截断 JSON。"""
    import copy
    def _issue_metadata_only(b):
        return {"issue_id": b["issue_id"], "code": b["code"],
                "anchor": b["anchor"],
                "evidence_ref": b["evidence_ref"]}

    def _budgeted(bundles_in, budget):
        """先全 metadata; 剩余预算按序分配 exact_context。"""
        items = []
        overhead = 0
        for b in bundles_in:
            meta = _issue_metadata_only(b)
            s = json.dumps(meta, ensure_ascii=False)
            overhead += len(s) + 60      # 结构开销余量
            items.append([meta, b.get("source")])
        remaining = max(budget - overhead, 0)
        per = max(remaining // max(len(items), 1), 80)
        out = []
        for meta, source in items:
            m = dict(meta)
            if source:
                m["source"] = {k: (v[:per] if k == "exact_context" else v)
                               for k, v in source.items()}
            out.append(m)
        return out

    budgeted = _budgeted(bundles, MAX_TOTAL_REPAIR_CONTEXT_CHARS)
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
            "character offsets into that exact_context). COPY_EVIDENCE_SLICE replaces "
            "only the quoted content — keep the surrounding quote markers/blockquote "
            "format intact. REPLACE_TEXT text is your own prose (paraphrase, citation "
            "fix) and also replaces only the content span. Do not output anything "
            "besides the JSON.\n\n"
            "ISSUES:\n" + json.dumps(budgeted, ensure_ascii=False))


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
        # H1 §2: patch 操作 content span; anchor_sha 合同 = content_sha256
        c_s = a.get("content_start", a.get("start", 0))
        c_e = a.get("content_end", a.get("end", 0))
        c_sha = a.get("content_sha256", a.get("surface_sha256"))
        if pt.get("anchor_sha256") != c_sha:
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
        spans.append((c_s, c_e, text, iid))
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


# ── O7-E RCA-1 H2 §C-F: COPY_SLICE_ID 合同——模型只选不数 ──
MAX_COPY_SLICES_PER_ISSUE = 12
MAX_COPY_SLICE_NORM_LENGTH = 240


def build_slice_catalog(bundles, locator, per_issue_locators=None):
    """机械生成 slice catalog: per-issue evidence 连续原始子串候选。

    H2C §5: per_issue_locators = {issue_id: locator}——每个 issue 的 slice
    用自己的 locator 排序（不再全局拼接）; Main Agent 选择权不变。"""
    catalog = {}
    for b in bundles:
        _loc = (per_issue_locators or {}).get(b["issue_id"], locator or "")
        qn = QB.norm_q(_loc)
        qsh = QB._shingles(qn) if qn else set()
        src = (b.get("source") or {})
        ctx = src.get("exact_context") or ""
        if not ctx:
            continue
        atoms = [a for a in re.split(r"(?<=[。！？；\n])|(?<=[，”」])", ctx) if a.strip()]
        if not atoms:
            atoms = [ctx]
        cands = []
        for i in range(len(atoms)):
            for span in (1, 2, 3):
                j = i + span
                if j > len(atoms):
                    break
                text = "".join(atoms[i:j])
                norm = QB.norm_q(text)
                if not (8 <= len(norm) <= MAX_COPY_SLICE_NORM_LENGTH):
                    continue
                ov = (len(qsh & QB._shingles(norm)) / len(qsh)) if qsh else 0
                cands.append({"text": text, "overlap": round(ov, 2)})
        seen = set()
        uniq = []
        for c in sorted(cands, key=lambda c: -c["overlap"]):
            if c["text"] in seen:
                continue
            seen.add(c["text"])
            uniq.append(c)
        catalog[b["issue_id"]] = [
            {"slice_id": f"{b['issue_id']}:s{k+1}", "text": c["text"],
             "overlap_score": c["overlap"]}
            for k, c in enumerate(uniq[:MAX_COPY_SLICES_PER_ISSUE])]
    return catalog


def render_patch_prompt_v2(bundles, slice_catalog, prev_errors=None):
    """H2 §C-D: 模型零 SHA/零 offset/零 evidence_ref 回显。
    RCA-2 §action: quote 动作拆分——COPY_SLICE（保留逐字引文形式）与
    PARAPHRASE_CLAIM（Main Agent 显式声明放弃逐字引文, claim 整体替换）;
    citation 仍用 COPY_SLICE / REPLACE_TEXT。"""
    def strip_meta(b):
        out = {"issue_id": b["issue_id"], "code": b["code"],
               "kind": "citation" if b.get("code") == "UNVERIFIED_CITATION"
               else "quote"}
        a = b.get("anchor") or {}
        out["anchor_preview"] = a.get("surface_preview", "")[:60]
        src = b.get("source") or {}
        if src.get("exact_context"):
            out["source_context"] = src["exact_context"][:400]
        if b["issue_id"] in slice_catalog:
            out["copy_slices"] = [{"slice_id": s["slice_id"], "text": s["text"][:240],
                                   "overlap_score": s["overlap_score"]}
                                  for s in slice_catalog[b["issue_id"]]]
        return out

    header = ("Repair the LOCAL issues below in your own previous final candidate. "
              "Output ONLY a JSON object:\n"
              '{"patches": [{"issue_id": "vi_N", "action": "COPY_SLICE", '
              '"slice_id": "vi_N:sK"} or {"issue_id": "vi_N", "action": '
              '"PARAPHRASE_CLAIM", "replacement_text": "..."} or '
              '{"issue_id": "vi_N", "action": "REPLACE_TEXT", '
              '"replacement_text": "..."}]}\n'
              "Action eligibility (strict):\n"
              "- kind=quote issues: COPY_SLICE or PARAPHRASE_CLAIM only. "
              "REPLACE_TEXT is invalid for quote issues.\n"
              "- kind=citation issues: COPY_SLICE or REPLACE_TEXT only. "
              "PARAPHRASE_CLAIM is invalid for citation issues.\n"
              "Rules: every issue listed must be covered by exactly one patch.\n"
              "COPY_SLICE replaces the quoted content with the exact bytes of the "
              "chosen slice (quote markers stay).\n"
              "PARAPHRASE_CLAIM (quote issues only) declares: this is no longer a "
              "verbatim quote. Your replacement_text replaces the ENTIRE claim "
              "including the surrounding quote marks / blockquote marker, and must "
              "not itself contain any verbatim quotation (write plain prose).\n"
              "REPLACE_TEXT (citation issues only) is your own prose replacing the "
              "citation content span.\n"
              "Do not compute offsets or copy any hash.\n")
    if prev_errors:
        header += ("\nprevious_patch_protocol_errors: " +
                   json.dumps(prev_errors[:6], ensure_ascii=False) +
                   "\n(fix the format accordingly)\n")
    items = [strip_meta(b) for b in bundles]
    return header + "\nISSUES:\n" + json.dumps(items, ensure_ascii=False)


def apply_main_agent_patches_v2(candidate, patch_json, bundles, slice_catalog,
                                context_candidate_sha=None, telemetry=None):
    """H2D §2: 无 SHA 回显版 applier——runtime 自验 candidate/anchor SHA。

    context_candidate_sha: build() 时记录的候选 SHA（模型不可见）; apply 前校验
    sha(current_candidate)==context SHA; 每 anchor 校验 target span SHA。
    FINAL-DIAG §5: telemetry 传入 list 时逐条 DECLARED patch 记录
    {issue_id, issue_code, anchor_kind, action, slice_id}——禁止 replacement_text/
    source 正文/CoT。
    RCA-2 §action: quote 动作语义拆分——
      COPY_SLICE      仅 quote/citation 通用: 替换 content_span（quote wrapper 保留）
      PARAPHRASE_CLAIM 仅 quote: Main Agent 显式声明放弃逐字引文 → 替换整个
                      claim_span（含 wrapper/blockquote 前缀一并移除）; replacement
                      本身不得再构成 QuoteBound 可识别的逐字引文
      REPLACE_TEXT    仅 citation（quote 上使用 → INVALID_ACTION_FOR_QUOTE, 零兼容）;
      PARAPHRASE_CLAIM 用于 citation → INVALID_ACTION_FOR_CITATION。"""

    def _rec(iid, action, slice_id=None):
        if telemetry is None:
            return
        b = next((x for x in bundles if x["issue_id"] == iid), None)
        code = (b or {}).get("code")
        telemetry.append({"issue_id": iid, "issue_code": code,
                          "anchor_kind": "citation"
                          if code == "UNVERIFIED_CITATION" else "quote",
                          "action": action, "slice_id": slice_id})
    try:
        p = json.loads(patch_json)
    except Exception:
        return None, ["INVALID_JSON"]
    if context_candidate_sha and _sha(candidate) != context_candidate_sha:
        return None, ["STALE_CANDIDATE"]
    errs = []
    covered = set()
    spans = []   # (start, end, text, iid, is_claim_span)
    cat_by_id = {s["slice_id"]: (s, iid) for iid, sl in slice_catalog.items()
                 for s in sl}
    for pt in p.get("patches") or []:
        iid = pt.get("issue_id")
        bundle = next((b for b in bundles if b["issue_id"] == iid), None)
        if bundle is None:
            errs.append(f"UNKNOWN_ISSUE_ID:{iid}")
            continue
        if iid in covered:
            errs.append(f"DUPLICATE_PATCH:{iid}")
            continue
        covered.add(iid)
        action = pt.get("action")
        _rec(iid, action,
             pt.get("slice_id") if action == "COPY_SLICE" else None)
        a = bundle.get("anchor")
        if not a:
            errs.append(f"NO_ANCHOR:{iid}")
            continue
        is_citation = bundle.get("code") == "UNVERIFIED_CITATION"
        # RCA-2 §action: quote/citation 动作资格（机械, 零兼容）
        if action == "REPLACE_TEXT" and not is_citation:
            errs.append(f"INVALID_ACTION_FOR_QUOTE:{iid}")
            continue
        if action == "PARAPHRASE_CLAIM":
            if is_citation:
                errs.append(f"INVALID_ACTION_FOR_CITATION:{iid}")
                continue
            text = pt.get("replacement_text")
            if not isinstance(text, str) or not text.strip():
                errs.append(f"EMPTY_REPLACEMENT:{iid}")
                continue
            # PARAPHRASE_CLAIM 不得重新制造 quote（机械 QB 门）
            if QB.extract_quotes(text):
                errs.append(f"PARAPHRASE_CONTAINS_VERBATIM_QUOTE:{iid}")
                continue
            t_s = a.get("claim_start", a.get("start", 0))
            t_e = a.get("claim_end", a.get("end", 0))
            # runtime anchor SHA 校验（target = claim span）
            _expected = a.get("claim_sha256") or a.get("content_sha256")
            if _expected and _sha(candidate[t_s:t_e])[:16] != _expected:
                errs.append(f"STALE_ANCHOR:{iid}")
                continue
            spans.append((t_s, t_e, text, iid, True))
            continue
        # COPY_SLICE / citation REPLACE_TEXT: target = content span
        c_s = a.get("content_start", a.get("start", 0))
        c_e = a.get("content_end", a.get("end", 0))
        # H2D §2: runtime anchor SHA 校验
        _expected = a.get("content_sha256") or a.get("surface_sha256")
        if _expected and _sha(candidate[c_s:c_e])[:16] != _expected:
            errs.append(f"STALE_ANCHOR:{iid}")
            continue
        if action == "COPY_SLICE":
            sid = pt.get("slice_id")
            hit = cat_by_id.get(sid)
            if hit is None or hit[1] != iid:
                errs.append(f"UNKNOWN_SLICE_ID:{sid}")
                continue
            text = hit[0]["text"]
        elif action == "REPLACE_TEXT":
            text = pt.get("replacement_text")
            if not isinstance(text, str) or not text.strip():
                errs.append(f"EMPTY_REPLACEMENT:{iid}")
                continue
        else:
            errs.append(f"UNKNOWN_ACTION:{action!r}:{iid}")
            continue
        spans.append((c_s, c_e, text, iid, False))
    for b in bundles:
        if b["issue_id"] not in covered:
            errs.append(f"UNPATCHED_ISSUE:{b['issue_id']}")
    if errs:
        return None, errs
    spans.sort(key=lambda t: -t[0])
    last_start = None
    for s, e, _, iid, _claim in spans:
        if last_start is not None and e > last_start:
            return None, [f"OVERLAP:{iid}"]
        last_start = s
    new = candidate
    for s, e, text, _, _claim in spans:
        new = new[:s] + text + new[e:]
    return new, []


def issue_fingerprint(code, locator, evidence_ref=None):
    """H2C §6: issue 指纹（code+norm locator+evidence_ref 三元组）。"""
    return hashlib.sha256(
        f"{code}|{QB.norm_q(locator or '')[:120]}|{evidence_ref or ''}".encode()
    ).hexdigest()[:16]


def all_issues_localizable(validation):
    """H2C §2: ALL issues 必须可局部化且可锚定 → LOCAL_PATCH; 否则 FULL_REWRITE。"""
    issues = validation.as_dict().get("issues", [])
    if not issues:
        return False
    return all((i or {}).get("code") in LOCAL_PATCH_CODES for i in issues)


def prepare_local_patch(candidate, validation, raw_tool_log, prev_errors=None):
    """H2D §1: LOCAL_PATCH preflight——三条件全过才 supported=true。

    (1) all issue codes local  (2) all anchors exact  (3) prompt structurally complete。
    返回 {supported, unsupported_reason, bundles, catalog, prompt, candidate_sha}。"""
    if not all_issues_localizable(validation):
        return {"supported": False, "unsupported_reason": "MIXED_OR_NON_LOCAL_ISSUES",
                "bundles": [], "catalog": {}, "prompt": "", "candidate_sha": None}
    bundles = build_repair_issue_bundles(candidate, validation, raw_tool_log)
    unanchored = [b["issue_id"] for b in bundles if not b.get("anchor")]
    if unanchored:
        return {"supported": False,
                "unsupported_reason": f"UNRESOLVED_ANCHORS:{','.join(unanchored[:4])}",
                "bundles": bundles, "catalog": {}, "prompt": "",
                "candidate_sha": None}
    issues = validation.as_dict().get("issues", [])
    per_loc = {b["issue_id"]: (i or {}).get("locator") or ""
               for b, i in zip(bundles, issues)}
    catalog = build_slice_catalog(bundles, "", per_issue_locators=per_loc)
    cand_sha = _sha(candidate)
    prompt = render_patch_prompt_v2(bundles, catalog, prev_errors)
    # prompt structural completeness: 所有 issue_id 在 prompt 中可见
    missing = [b["issue_id"] for b in bundles
               if b["issue_id"] not in prompt]
    coverage = round((len(bundles) - len(missing)) / max(len(bundles), 1), 3)
    if missing:
        return {"supported": False,
                "unsupported_reason": f"PROMPT_ISSUE_INVISIBLE:{','.join(missing[:4])}",
                "bundles": bundles, "catalog": catalog, "prompt": prompt,
                "candidate_sha": cand_sha, "prompt_issue_coverage": coverage}
    return {"supported": True, "unsupported_reason": None, "bundles": bundles,
            "catalog": catalog, "prompt": prompt, "candidate_sha": cand_sha,
            "prompt_issue_coverage": coverage}
