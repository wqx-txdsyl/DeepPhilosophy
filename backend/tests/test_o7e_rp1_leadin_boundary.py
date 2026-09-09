# -*- coding: utf-8 -*-
"""O7-E RCA-2 RP1 Lead-in Demotion Integrity: L1-L6 回归。

锁死（Reviewer 2026-09-09 RCA-2 审查 §BLOCKER=LEADIN_PARAPHRASE_CLAIM_BOUNDARY）:
  L1 原文如下："fake" → PARAPHRASE 后 "原文如下" 与引号域一起消失
  L2 孔子写道："fake" → "孔子写道：" 这一 verbatim lead-in 一起被 claim 替换
  L3 同一 leadin COPY_SLICE → lead-in + quote delimiters 全部原样保留
  L4 claim-span 外字节完全不变
  L5 无法机械确定 lead-in boundary → 不允许 quote-only PARAPHRASE（返回 None）
  L6 QuoteBound extraction / EXACT / NEAR / MEMORY_ONLY semantics zero diff
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import repair_context as RC
import quote_bound as QB

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_o7e_h2c_contract import _raw_log, _sha

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_FAKE = "伪造的引文措辞并非库中原文"


def _fixtures(cand):
    from final_validator import validate_final_candidate
    v = validate_final_candidate(cand, raw_tool_log=_raw_log(),
                                 fallback_log=[], language="zh")
    issues = v.as_dict().get("issues", [])
    assert any(i.get("code") == "UNSUPPORTED_EXACT_QUOTE" for i in issues), issues
    bundles = RC.build_repair_issue_bundles(cand, v, _raw_log())
    per_loc = {f"vi_{k+1}": (i or {}).get("locator") or ""
               for k, i in enumerate(issues)}
    catalog = RC.build_slice_catalog(bundles, "", per_issue_locators=per_loc)
    qt = bundles[0]
    return qt, catalog


_PARA = "这里可以理解为作者在强调遵循成规的处世态度。"

# L1/L3/L4 共用: 原文如下："fake"
CAND_L1 = "开篇一段正文。\n\n原文如下：“" + _FAKE + "”此后正文继续。"


def _apply_paraphrase(cand, qt, catalog, para=_PARA):
    patch = json.dumps({"patches": [
        {"issue_id": qt["issue_id"], "action": "PARAPHRASE_CLAIM",
         "replacement_text": para}]}, ensure_ascii=False)
    return RC.apply_main_agent_patches_v2(cand, patch, [qt], catalog)


def test_l1_yuanwen_leadin_removed_with_quote_domain():
    qt, catalog = _fixtures(CAND_L1)
    assert qt["anchor"]["quote_kind"] == "leadin"
    new, errs = _apply_paraphrase(CAND_L1, qt, catalog)
    assert new is not None, errs
    assert "原文如下" not in new
    assert "“" not in new and "”" not in new
    assert _FAKE not in new
    assert _PARA in new


def test_l2_subject_leadin_removed_together():
    cand = "孔子写道：“" + _FAKE + "”此后正文继续。"
    qt, catalog = _fixtures(cand)
    new, errs = _apply_paraphrase(cand, qt, catalog)
    assert new is not None, errs
    assert "孔子写道" not in new            # 主体+引导语整体随 claim 替换
    assert "“" not in new and _FAKE not in new
    assert _PARA in new


def test_l3_leadin_copy_slice_preserves_leadin_and_delimiters():
    # NEAR leadin 引文（与证据高重叠）→ best-effort source/slices 存在
    cand = "原文如下：“夫人不言，言必有种。”此后正文继续。"
    qt, catalog = _fixtures(cand)
    assert qt["anchor"]["quote_kind"] == "leadin"
    slices = catalog.get(qt["issue_id"]) or []
    assert slices, "NEAR leadin fixture 必须有 best-effort source/slices"
    patch = json.dumps({"patches": [
        {"issue_id": qt["issue_id"], "action": "COPY_SLICE",
         "slice_id": slices[0]["slice_id"]}]}, ensure_ascii=False)
    new, errs = RC.apply_main_agent_patches_v2(cand, patch, [qt], catalog)
    assert new is not None, errs
    a = qt["anchor"]
    # content 之前的所有字节（含 原文如下： 与开引号）原样保留
    assert new[:a["content_start"]] == cand[:a["content_start"]]
    assert new[a["content_start"] + len(slices[0]["text"]):] \
        == cand[a["content_end"]:]
    assert new[a["content_start"]:a["content_start"] + len(slices[0]["text"])] \
        == slices[0]["text"]


def test_l4_bytes_outside_claim_span_unchanged():
    qt, catalog = _fixtures(CAND_L1)
    new, errs = _apply_paraphrase(CAND_L1, qt, catalog)
    assert new is not None
    a = qt["anchor"]
    expected = CAND_L1[:a["claim_start"]] + _PARA + CAND_L1[a["claim_end"]:]
    assert new == expected


def test_l5_unresolvable_leadin_boundary_never_quote_only_claim():
    # kind=leadin 但 quote 前不存在 $ 锚定的紧邻引导语 → _claim_content_span
    # 返回 None（上游 _quote_anchor 据此拒绝给锚 → preflight unsupported →
    # FULL_REWRITE——绝不以 quote-only claim 偷偷留下 verbatim 引导语）
    cand = "这里没有任何引导词。“" + _FAKE + "”"
    qs = cand.find("“")
    q = {"kind": "leadin", "text": _FAKE,
         "char_start": qs, "char_end": qs + len(_FAKE) + 2}
    assert RC._claim_content_span(cand, q) is None


def test_l6_quote_bound_semantics_zero_diff():
    r = subprocess.run(["git", "diff", "--quiet", "afe8a1c70", "--",
                        "backend/quote_bound.py"], cwd=ROOT, capture_output=True)
    assert r.returncode == 0, "quote_bound 相对 RCA-2 BASE 有改动（本阶段禁止）"
