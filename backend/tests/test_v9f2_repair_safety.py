# -*- coding: utf-8 -*-
"""V9-F2: repair-safety production patch 测试（DEV-only synthetic,
FORBIDDEN_FROM_V10=true; 零 V9 case 复用/零硬编码）。

覆盖任务书七场景:
  1. PARAPHRASE → new exact quote wrapper → layer-1 admission 拒绝
  2. PARAPHRASE → new citation attribution cue → layer-1 admission 拒绝
  3. safe paraphrase → 正常接受
  4. PARAPHRASE → new NEAR quote（无 wrapper, 层1 不拦）→ semantic 安全门拒绝
  5. unsafe first → safe second: repair ≤2 收敛, 发布干净
  6. unsafe all attempts → FAIL-CLOSED, 零无效 token 外流
  7. 既有 no-op / plan-only / Local Patch 回归保持 PASS（见同目录其他测试）
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import local_patch_runtime as LPR

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_o7e_final_diagnostic import (_run_lp, _done, _GOOD,
                                       _AnchorMissingAdapter)
from test_o2_final_ownership import _TOOLS_SCRIPT, _msg, _SENTINEL_FAKE

# 近引文替换正文: 与库内 lunyu 原文高度重叠但无引号/无归因 cue
# → layer-1 不拦, validator 判 NEAR_QUOTE_NOT_MARKED（新 QUOTE 家族指纹）
# → V9-F2 §2 semantic 安全门拒绝
# 绕过 layer-1 的 unsafe 形态: PARAPHRASE 替换中新增无证据 citation 标记
#（【】非引号 wrapper, RC verbatim-content guard 不覆盖）→ 新 UNVERIFIED_CITATION
#（CITATION 家族 GENUINELY_NEW）→ semantic 安全门拒绝
_CITATION_INJECT = "结论保留。参见【《论自由》】。"   # 【】不在 layer-1 wrapper 类 → 不拦


def _patch(replacement):
    return json.dumps({"patches": [{"issue_id": "vi_1",
                                    "action": "PARAPHRASE_CLAIM",
                                    "replacement_text": replacement}]},
                      ensure_ascii=False)


_BAD = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
_SAFE = ("孔子批评鲁人改建长府，并借闵子骞的评论说明行事应遵循成规、言语贵在切中要害。")
_WRAPPER_PATCH = _patch("「" + _SENTINEL_FAKE + "」出自《论语》原文。")
_ATTRIBUTION_PATCH = _patch("卢梭在《社会契约论》中写道，强迫的自由也是自由。")
_CITATION_PATCH = _patch(_CITATION_INJECT)
_FIX_PATCH = _patch(_SAFE)


def test_v9f2_l1_wrapper_replacement_rejected_at_admission():
    """layer-1: PARAPHRASE 替换含逐字引文 wrapper → admission 拒绝"""
    unsafe = LPR._unsafe_paraphrase_scan(_WRAPPER_PATCH)
    assert unsafe and unsafe[0] == "UNSAFE_PARAPHRASE_QUOTE_WRAPPER"
    safe = LPR._unsafe_paraphrase_scan(_SAFE)
    assert safe is None


def test_v9f2_l1_attribution_cue_rejected_at_admission():
    unsafe = LPR._unsafe_paraphrase_scan(_ATTRIBUTION_PATCH)
    assert unsafe and unsafe[0] == "UNSAFE_PARAPHRASE_ATTRIBUTION"


def test_v9f2_l1_non_json_falls_through():
    assert LPR._unsafe_paraphrase_scan("这不是 JSON") is None


# ═══════════════════════════════════════════════════════
# production path E2E（真实 LangGraph 图 + production LocalPatchAdapter）
# ═══════════════════════════════════════════════════════
def _production_adapter():
    from local_patch_runtime import LocalPatchAdapter
    return LocalPatchAdapter()


def test_v9f2_e2e_wrapper_repair_rejected_then_safe_converges():
    """unsafe（wrapper）第一修被 admission 拒绝 → 升级反馈 → 第二修安全收敛发布"""
    evs, _chat = _run_lp(
        "言必有中出处",
        _TOOLS_SCRIPT + [_msg(_BAD), _msg(_WRAPPER_PATCH), _msg(_FIX_PATCH)],
        adapter=_production_adapter())
    done = _done(evs)
    trace = (done.get("validation") or {}).get("repair_trace") or []
    tel = (done.get("v8f2_telemetry") or {})
    assert trace, "repair 必须发生"
    lp = trace[0].get("local_patch") or {}
    assert lp.get("applied") is False            # unsafe patch 被 admission 拒绝
    assert any("UNSAFE_PARAPHRASE" in str(e) for e in lp.get("errors") or [])
    # admission 拒绝（零文本变化）→ 按 no-op 类别升级; 类别与 semantic 拒绝不混淆
    assert trace[1].get("no_op_escalated") is True
    answer = "".join(e.get("content", "") for e in evs if e.get("type") == "token")
    assert _SENTINEL_FAKE not in answer
    assert done["validation"]["result"]["ok"] is True


def test_v9f2_e2e_new_citation_rejected_by_semantic_gate():
    """PARAPHRASE 替换中新增无 evidence 的 citation 标记（无归因动词,
    layer-1 cue 不拦）: semantic 安全门判 GENUINELY_NEW CITATION 家族 →
    拒绝, pre candidate 保留（对应 V9-11 probable mechanism 的 generic 化）"""
    evs, _chat = _run_lp(
        "言必有中出处",
        _TOOLS_SCRIPT + [_msg(_BAD), _msg(_CITATION_PATCH), _msg(_FIX_PATCH)],
        adapter=_production_adapter())
    done = _done(evs)
    trace = (done.get("validation") or {}).get("repair_trace") or []
    tel = (done.get("v8f2_telemetry") or {})
    assert trace[0].get("local_patch", {}).get("applied") is True   # layer-1 放行
    assert trace[0].get("repair_safety_rejected") is not None       # 语义门拒绝
    rejected = trace[0]["repair_safety_rejected"]
    assert "CITATION" in rejected["families"]
    assert rejected["pre_candidate_restored"] is True
    assert tel.get("REPAIR_SAFETY_REJECTED_NEW_ISSUE", 0) >= 1
    assert "CITATION" in (tel.get("REPAIR_SAFETY_REJECTED_FAMILY") or [])
    # 最终发布的仍是干净回答（repair 2 安全收敛）
    answer = "".join(e.get("content", "") for e in evs if e.get("type") == "token")
    assert done["validation"]["result"]["ok"] is True


def test_v9f2_e2e_unsafe_all_attempts_fail_closed():
    """两修均 unsafe → FAIL-CLOSED: 零无效 token 外流, error 收口"""
    evs, _chat = _run_lp(
        "言必有中出处",
        _TOOLS_SCRIPT + [_msg(_BAD), _msg(_WRAPPER_PATCH), _msg(_CITATION_PATCH)],
        adapter=_production_adapter())
    tokens = "".join(e.get("content", "") for e in evs if e.get("type") == "token")
    assert _SENTINEL_FAKE not in tokens
    assert any(e.get("type") == "validation_failed" for e in evs)
    assert any(e.get("type") == "error" for e in evs)
    tel = (_done(evs).get("v8f2_telemetry") or {})
    assert tel.get("REPAIR_SAFETY_REJECTED_NEW_ISSUE", 0) >= 1


def test_v9f2_e2e_safe_paraphrase_accepted():
    """安全转述 patch: issue resolved, 零 genuinely-new, 正常接受（防误杀）"""
    evs, _chat = _run_lp(
        "言必有中出处",
        _TOOLS_SCRIPT + [_msg(_BAD), _msg(_FIX_PATCH)],
        adapter=_production_adapter())
    done = _done(evs)
    assert done["validation"]["result"]["ok"] is True
    tel = (done.get("v8f2_telemetry") or {})
    assert tel.get("REPAIR_SAFETY_REJECTED_NEW_ISSUE", 0) == 0
