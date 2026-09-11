# -*- coding: utf-8 -*-
"""O7-E Production Freeze §A: Local Patch 生产 adapter 单一所有者。

从 tools/evaluation/o7e_rca1_hook_eval.py 晋升——生产路径（General Agent）与
评测 runner 共用同一个 adapter 实现（LOCAL_PATCH_ADAPTER_OWNER=1）。
职责边界: prepare() / parse_and_apply() / 机械遥测——零认知权
（认知权全部属于 Main Agent; RUNTIME_GENERATED_PROSE_CHARS=0）。
"""
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import repair_context as RC
import quote_bound as QB

QUOTE_CODES = {"UNSUPPORTED_EXACT_QUOTE", "NEAR_QUOTE_NOT_MARKED", "STITCHED_QUOTE"}

# ══ V9-F2-R1 §4: quote-safe PARAPHRASE_CLAIM 合同（generic, 零 case-specific,
# 收紧版）═══
# PARAPHRASE 替换正文必须是转述。blockable cue 收敛为明确逐字/精确出处类
# （任务书清单）: 原文写道/原文说/语录/第N章/第N页/p./pp.;
# 普通转述动词（指出/认为/主张/写道）不再仅凭动词判 unsafe;
# ASCII ' 与 curly ' 不作为单字符 wrapper（缩约/所有格不误杀, 如 doesn't /
# Arendt's）; 单引号仅成对包围非空 span 时判 unsafe。零 NER/零第二套 classifier。
# V9-F2-R2 §2: wrapper/cue 边界收紧——
# - ASCII ' 与 curly ’ 不作单字符 wrapper（缩约 doesn't/所有格 Arendt's/
#   复数所有格 students' 均不误杀: 词邻 apostrophe 先剥离再判成对）;
# - 成对单引号含 ASCII 对（'...')与 typographic 对（‘...’）, 且要求
#   非空 span（防止 '' 空引号空触发）;
# - cue 收敛任务书清单: 原文写道/原文说/语录/第N章/第N页/p.N;
#   普通转述动词（写道/指出/认为/主张/曾说）不拦。
_PARAPHRASE_WRAPPER_RE = re.compile("[\u300c\u300d\u300e\u300f\u201c\u201d]")
# 成对单引号（ASCII 对 + typographic ‘’ 对）: opening 前不得是字母（词内缩约/
# 所有格如 doesn't/Arendt's/students' 的 apostrophe 词邻字母 → 不构成 opening）,
# closing 后不得是字母; 中间非空非换行 → quotation wrapper。零 NER/零 LLM。
_PAIRED_SINGLE_RE = re.compile(r"(?<![A-Za-z])['’][^'’\n]{1,}?['’](?![A-Za-z])")
_PAIRED_CURLY_SINGLE_RE = re.compile('‘[^‘’\n]{1,}’')
_PARAPHRASE_CUE_RE = re.compile(
    r"原文写道|原文说|原文中|语录|收录于"
    r"|第\s*[0-9一二三四五六七八九十]+\s*[章节页]|pp?\.\s*[0-9]+")


def _unsafe_paraphrase_scan(model_output):
    """扫描 patch JSON 中 PARAPHRASE_CLAIM 的 replacement_text;
    返回 (error_code, bounded_prefix) 或 None（无违规/非 JSON→交给正常错误路径）。

    - wrapper: CJK/双引号 wrapper 字符直接 unsafe;
    - 单引号: 剥离词内缩约/所有格 apostrophe 后成对包围非空 span → unsafe;
    - cue: 明确逐字/精确出处措辞（原文写道/原文说/语录/第N章/第N页/p. N）unsafe;
      普通转述动词（指出/认为/主张/写道）不拦。"""
    try:
        obj = json.loads(model_output)
    except Exception:
        return None
    patches = obj.get("patches") if isinstance(obj, dict) else None
    if not isinstance(patches, list):
        return None
    for p in patches:
        if not isinstance(p, dict) or p.get("action") != "PARAPHRASE_CLAIM":
            continue
        text = str(p.get("replacement_text") or "")
        if _PARAPHRASE_WRAPPER_RE.search(text):
            return ("UNSAFE_PARAPHRASE_QUOTE_WRAPPER", text[:120])
        if _PAIRED_SINGLE_RE.search(text):
            return ("UNSAFE_PARAPHRASE_QUOTE_WRAPPER", text[:120])
        if _PAIRED_CURLY_SINGLE_RE.search(text):
            return ("UNSAFE_PARAPHRASE_QUOTE_WRAPPER", text[:120])
        if _PARAPHRASE_CUE_RE.search(text):
            return ("UNSAFE_PARAPHRASE_ATTRIBUTION", text[:120])
    return None


class LocalPatchAdapter:
    """candidate-aware prepare 单入口（三条件 preflight 由 RC.prepare_local_patch
    判定）; supported=False 时 engine 必须走 FULL_REWRITE。"""

    def prepare(self, candidate, validation, raw_tool_log, prev_errors=None):
        prep = RC.prepare_local_patch(candidate, validation, raw_tool_log, prev_errors)
        issues = validation.as_dict().get("issues", [])
        fps = [RC.issue_fingerprint((i or {}).get("code"),
                                    (i or {}).get("locator") or "",
                                    (i or {}).get("evidence_ref"))
               for i in issues]
        out = dict(prep)
        out["pre_patch_candidate"] = candidate
        out["issue_fps"] = fps
        return out

    def parse_and_apply(self, pre_candidate, model_output, ctx):
        if not ctx.get("rebind_ok", True):
            return None, ["LOCAL_PATCH_UNSUPPORTED: rebind"], {}
        # V9-F2 §1: PARAPHRASE 替换文本安全合同（admission 层机械扫描;
        # 拒绝 → apply 失败 → engine 回退 pre candidate 并给安全升级反馈）
        unsafe = _unsafe_paraphrase_scan(model_output)
        if unsafe:
            code, prefix = unsafe
            return None, [f"{code}: {prefix}"], {
                "paraphrase_safety_rejected": {"code": code, "prefix": prefix}}
        telemetry = []
        new, errs = RC.apply_main_agent_patches_v2(
            pre_candidate, model_output, ctx.get("bundles") or [],
            ctx.get("catalog") or {},
            context_candidate_sha=ctx.get("candidate_sha"), telemetry=telemetry)
        # 指纹补全（bundle 序 == issue 序, vi_N ↔ fps[N-1]）; 零正文记录
        fps = ctx.get("issue_fps") or []
        for rec in telemetry:
            try:
                n = int(str(rec.get("issue_id", "")).split("_")[-1])
                rec["issue_fingerprint"] = fps[n - 1] if 1 <= n <= len(fps) else None
            except Exception:
                rec["issue_fingerprint"] = None
        # wrapper 遥测: 有意降级 ≠ 非预期 wrapper 丢失
        intentional = 0
        unintentional_loss = 0
        nt_violations = 0
        target_spans = []
        lost = 0
        if new is not None:
            target_claims = []
            for rec in telemetry:
                b = next((x for x in (ctx.get("bundles") or [])
                          if x["issue_id"] == rec.get("issue_id")), None)
                a = (b or {}).get("anchor") or {}
                qs, qe = a.get("claim_start"), a.get("claim_end")
                cs, ce = a.get("content_start"), a.get("content_end")
                if None not in (qs, qe):
                    target_claims.append((qs, qe))
                if rec.get("action") == "PARAPHRASE_CLAIM":
                    intentional += 1
                    if None not in (qs, qe):
                        target_spans.append((qs, qe))
                    # 降级机械事实: wrapper 子串应从新候选消失
                    if (qs is not None and cs is not None and qs < cs
                            and pre_candidate[qs:cs]
                            and pre_candidate[qs:cs] in new):
                        rec["wrapper_retained"] = True
                    continue
                if cs is None or ce is None:
                    continue
                target_spans.append((cs, ce))
                if rec.get("anchor_kind") != "quote":
                    continue
                # COPY_SLICE(quote): wrapper 必须保留——消失 = 非预期丢失
                if qs is not None and qs < cs and pre_candidate[qs:cs] \
                        and pre_candidate[qs:cs] not in new:
                    unintentional_loss += 1
                if qe is not None and ce is not None and ce < qe \
                        and pre_candidate[ce:qe] and pre_candidate[ce:qe] not in new:
                    unintentional_loss += 1
            if RC.non_target_changed_chars(pre_candidate, new,
                                           target_spans) != 0:
                nt_violations = 1
            # 目标外已验证 quote byte-preserved（anti-gaming）
            raw_log = ctx.get("raw_tool_log")
            if raw_log is not None:
                audit = QB.audit_quotes(pre_candidate, raw_log)
                ext = QB.extract_quotes(pre_candidate)
                for e, q in zip(audit.get("entries", []), ext):
                    if e.get("verification_state") not in ("VERIFIED_EXACT",
                                                           "VERIFIED_NEAR"):
                        continue
                    qs2, qe2 = q.get("char_start"), q.get("char_end")
                    if qs2 is None:
                        continue
                    if any(not (qe2 <= ts or qs2 >= te)
                           for ts, te in target_claims):
                        continue
                    if q.get("text") not in new:
                        lost += 1
        return new, (errs or []), {
            "actions": telemetry,
            "intentional_quote_to_paraphrase": intentional,
            "unintentional_quote_wrapper_loss": unintentional_loss,
            "preexisting_verified_quotes_lost": lost,
            "non_target_changed": nt_violations}


class _ProductionAdapterSingleton:
    instance = None


def production_adapter():
    """General Agent 生产路径单例（engine 默认注入; 评测 runner 同源引用）。"""
    if _ProductionAdapterSingleton.instance is None:
        _ProductionAdapterSingleton.instance = LocalPatchAdapter()
    return _ProductionAdapterSingleton.instance
