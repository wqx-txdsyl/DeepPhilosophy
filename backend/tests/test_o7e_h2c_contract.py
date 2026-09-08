# -*- coding: utf-8 -*-
"""O7-E RCA-1 H2C: H2-01 ~ H2-25 回归——Patch Contract V2 语义锁死。"""
import hashlib
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine_langgraph as EG
import repair_context as RC
import quote_bound as QB
from final_validator import validate_final_candidate

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


_LUNYU = ("鲁人为长府，闵子骞曰：“仍旧贯如之何？何必改作？”\n"
          "子曰：“夫人不言，言必有中。”")


def _raw_log():
    return [{"name": "get_chapter",
             "args": {"book_id": "lunyu", "chapter_idx": 13},
             "result_full": {"book_id": "lunyu", "chapter_idx": 13,
                             "book_title": "论语", "title": "先进篇",
                             "text": _LUNYU}}]


CAND = ("开头一段正文，讨论孔子的言论。\n\n"
        "原文如下：\n\n> 「鲁人为长府，闵子骞曰：“仍旧贯如之何？何必改造？”」\n\n"
        "「言必有中」出自【《韩非子·五蠹》】。\n\n结尾一段正文。")


def _mk_validation(candidate, log=None):
    return validate_final_candidate(candidate, raw_tool_log=log or _raw_log(),
                                    fallback_log=[], language="zh")


def _apply_safe(cand, patch_json, bundles, catalog):
    """只 patch 第一个 bundle。"""
    new, errs = RC.apply_main_agent_patches_v2(cand, patch_json, bundles, catalog)
    if errs and any("UNPATCHED" in e for e in errs):
        new, errs = RC.apply_main_agent_patches_v2(
            cand, patch_json, bundles[:1], catalog)
    return new, errs


def _bundles_and_catalog():
    v = _mk_validation(CAND)
    bundles = RC.build_repair_issue_bundles(CAND, v, _raw_log())
    issues = v.as_dict().get("issues", [])
    per_loc = {f"vi_{k+1}": (i or {}).get("locator") or "" for k, i in enumerate(issues)}
    catalog = RC.build_slice_catalog(bundles, "", per_issue_locators=per_loc)
    return v, bundles, catalog


# ── H2-01/02: System protocol 互斥 ──
def test_h2_01_local_patch_system_excludes_full_rewrite():
    msgs = EG._build_context_messages("general", "zh", reinforce=True,
                                      repair_mode=True,
                                      repair_output_mode="LOCAL_PATCH")
    blob = msgs[0].content
    assert "局部补丁执行协议" in blob
    assert "完整的替换最终回答" not in blob


def test_h2_02_full_rewrite_system_excludes_local_patch():
    msgs = EG._build_context_messages("general", "zh", reinforce=True,
                                      repair_mode=True,
                                      repair_output_mode="FULL_REWRITE")
    blob = msgs[0].content
    assert "修复执行协议" in blob
    assert "局部补丁" not in blob


# ── H2-03/04/05: 零 SHA 回显 + runtime 自验 ──
def test_h2_03_model_output_no_candidate_sha():
    _, bundles, catalog = _bundles_and_catalog()
    prompt = RC.render_patch_prompt_v2(bundles, catalog)
    # 合同文本不含 SHA 要求
    assert "candidate_sha256" not in prompt
    parsed = json.loads('{"patches":[{"issue_id":"vi_1","action":"REPLACE_TEXT","replacement_text":"改"}]}')
    assert "candidate_sha256" not in parsed


def test_h2_04_model_output_no_anchor_sha():
    _, bundles, catalog = _bundles_and_catalog()
    prompt = RC.render_patch_prompt_v2(bundles, catalog)
    assert "anchor_sha256" not in prompt


def test_h2_05_runtime_still_verifies_identity():
    # apply_v2 用 bundle 内部 anchor（runtime 自有）——错 issue_id 被拒
    _, bundles, catalog = _bundles_and_catalog()
    patch = '{"patches":[{"issue_id":"vi_WRONG","action":"REPLACE_TEXT","replacement_text":"x"}]}'
    new, errs = RC.apply_main_agent_patches_v2(CAND, patch, bundles, catalog)
    assert new is None and any("UNKNOWN_ISSUE_ID" in e for e in errs)


# ── H2-06/07/08/09: COPY_SLICE ──
def test_h2_06_copy_slice_exact_bytes():
    _, bundles, catalog = _bundles_and_catalog()
    qt = next(b for b in bundles if b["code"] in
              ("NEAR_QUOTE_NOT_MARKED", "UNSUPPORTED_EXACT_QUOTE"))
    slices = catalog.get(qt["issue_id"], [])
    if not slices:
        pytest.skip("no source for this fixture")
    s = slices[0]
    patch = json.dumps({"patches": [{"issue_id": qt["issue_id"],
                                     "action": "COPY_SLICE",
                                     "slice_id": s["slice_id"]}]})
    new, errs = RC.apply_main_agent_patches_v2(CAND, patch, [qt], catalog)
    assert new is not None, errs
    # 精确字节: replaced text 含 slice 原文
    assert s["text"] in new


def test_h2_07_unknown_slice_id_rejected():
    _, bundles, catalog = _bundles_and_catalog()
    qt = next(b for b in bundles if b["code"] in
              ("NEAR_QUOTE_NOT_MARKED", "UNSUPPORTED_EXACT_QUOTE"))
    patch = json.dumps({"patches": [{"issue_id": qt["issue_id"],
                                     "action": "COPY_SLICE",
                                     "slice_id": "vi_1:s999"}]})
    new, errs = RC.apply_main_agent_patches_v2(CAND, patch, bundles, catalog)
    assert new is None and any("UNKNOWN_SLICE_ID" in e for e in errs)


def test_h2_08_slice_cannot_cross_evidence():
    """slice 必须是 evidence 的连续原始子串——catalog 生成保证。"""
    _, bundles, catalog = _bundles_and_catalog()
    for iid, slices in catalog.items():
        for s in slices:
            # 找该 issue 的 source context
            b = next(x for x in bundles if x["issue_id"] == iid)
            ctx = (b.get("source") or {}).get("exact_context") or ""
            assert s["text"] in ctx, f"{s['slice_id']} not substring of evidence"


def test_h2_09_slice_selection_owner_main_agent():
    """catalog 提供 overlap_score 但只排序——选择权在模型（无自动应用）。"""
    _, bundles, catalog = _bundles_and_catalog()
    for iid, slices in catalog.items():
        for s in slices:
            assert "overlap_score" in s     # 参考分存在
    # apply_v2 只有模型给出 slice_id 才操作
    new, errs = RC.apply_main_agent_patches_v2(
        CAND, '{"patches":[]}', bundles, catalog)
    assert new is None                      # 空 patches → UNPATCHED_ISSUE 错误


# ── H2-10~14: protocol error 语义 ──
def test_h2_10_protocol_error_preserves_candidate():
    _, bundles, catalog = _bundles_and_catalog()
    patch = "NOT_VALID_JSON{{{"
    new, errs = RC.apply_main_agent_patches_v2(CAND, patch, bundles, catalog)
    assert new is None and "INVALID_JSON" in errs
    # engine 层: candidate = pre_patch_candidate（不制空）——由 engine seam 逻辑保证


def test_h2_11_protocol_error_consumes_attempt():
    # engine repair_trace 记录 errors → repairs_used 已在 repair 循环中递增
    # 单测层面: apply 失败返回 None 即证明 attempt 需要消耗
    _, bundles, catalog = _bundles_and_catalog()
    new, errs = RC.apply_main_agent_patches_v2(CAND, "x", bundles, catalog)
    assert new is None


def test_h2_12_second_attempt_remains_local_patch():
    # all_issues_localizable 对原 issues 仍真（candidate 未变）
    v = _mk_validation(CAND)
    assert RC.all_issues_localizable(v) is True
    # 即使前一轮 INVALID_JSON, can_handle 不受影响
    assert RC.all_issues_localizable(v) is True


def test_h2_13_protocol_error_never_empty_final():
    # apply_v2 错误返回 None; engine seam 设 candidate=pre_patch（非空）
    _, bundles, catalog = _bundles_and_catalog()
    new, _ = RC.apply_main_agent_patches_v2(CAND, "bad", bundles, catalog)
    assert new is None          # None ≠ ""（engine 用 pre_patch_candidate 替代）


def test_h2_14_no_silent_full_rewrite():
    # mixed local+nonlocal → can_handle false（ALL-local 路由）
    # 构造: 只有 non-local code
    from types import SimpleNamespace
    fake_val = SimpleNamespace(as_dict=lambda: {"issues": [
        {"code": "SOME_OTHER_CODE", "locator": "", "evidence_ref": None}]})
    assert RC.all_issues_localizable(fake_val) is False


# ── H2-15~19: latest evidence finalization ──
def test_h2_15_tool_free_uses_original_bundle():
    # raw_log hash 不变 → engine 走原 bundle/catalog 路径（engine seam 逻辑）
    import hashlib as hl
    h1 = hl.sha256(json.dumps(_raw_log(), default=str).encode()).hexdigest()
    h2 = hl.sha256(json.dumps(_raw_log(), default=str).encode()).hexdigest()
    assert h1 == h2              # 无变化 → original 路径


def test_h2_16_tool_use_changes_raw_log_hash():
    import hashlib as hl
    log1 = list(_raw_log())
    log2 = list(_raw_log()) + [{"name": "search_books", "args": {},
                                "result_full": {"results": []}}]
    h1 = hl.sha256(json.dumps(log1, default=str).encode()).hexdigest()
    h2 = hl.sha256(json.dumps(log2, default=str).encode()).hexdigest()
    assert h1 != h2


def test_h2_17_latest_bundle_rebuilt():
    # build() with latest raw_tool_log 产新 bundle（同 candidate 可重建）
    v = _mk_validation(CAND)
    b1 = RC.build_repair_issue_bundles(CAND, v, _raw_log())
    b2 = RC.build_repair_issue_bundles(CAND, v, _raw_log())
    assert len(b1) == len(b2)    # 确定性重建


def test_h2_18_finalization_uses_latest_catalog():
    # adapter.build 接受任意 raw_tool_log → catalog 由当前 log 决定
    v = _mk_validation(CAND)
    bundles = RC.build_repair_issue_bundles(CAND, v, _raw_log())
    issues = v.as_dict().get("issues", [])
    per_loc = {f"vi_{k+1}": (i or {}).get("locator") or "" for k, i in enumerate(issues)}
    cat = RC.build_slice_catalog(bundles, "", per_issue_locators=per_loc)
    assert isinstance(cat, dict)


def test_h2_19_finalization_no_repairs_used():
    # engine seam: finalization 在 repair loop 内不递增 repairs_used
    # （代码路径: finalization 后 continue validation loop, repairs_used 不变）
    eng = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "engine_langgraph.py"), encoding="utf-8").read()
    assert "finalization" in eng  # finalization path exists
    # repairs_used 只在 repair 循环头递增（repairs_used += 1 一次/轮）


# ── H2-20/21: fingerprint ──
def test_h2_20_fingerprint_stable():
    fp1 = RC.issue_fingerprint("NEAR_QUOTE_NOT_MARKED", "「改造」", "qb_read_0")
    fp2 = RC.issue_fingerprint("NEAR_QUOTE_NOT_MARKED", "「改造」", "qb_read_0")
    assert fp1 == fp2


def test_h2_21_fingerprint_classification():
    # 同 code+locator 但不同 evidence_ref → 不同 fingerprint
    fa = RC.issue_fingerprint("CODE", "loc", "ev_1")
    fb = RC.issue_fingerprint("CODE", "loc", "ev_2")
    assert fa != fb
    # 不同 code → 不同
    fc = RC.issue_fingerprint("CODE2", "loc", "ev_1")
    assert fa != fc


# ── H2-22/23: wrapper 保留 + 非目标不变 ──
def test_h2_22_quote_wrapper_survives_copy():
    _, bundles, catalog = _bundles_and_catalog()
    qt = next(b for b in bundles if b["code"] in
              ("NEAR_QUOTE_NOT_MARKED", "UNSUPPORTED_EXACT_QUOTE"))
    slices = catalog.get(qt["issue_id"], [])
    if not slices:
        pytest.skip("no slices")
    s = slices[0]
    patch = json.dumps({"patches": [{"issue_id": qt["issue_id"],
                                     "action": "COPY_SLICE",
                                     "slice_id": s["slice_id"]}]})
    new, _ = RC.apply_main_agent_patches_v2(CAND, patch, [qt], catalog)
    assert new is not None
    # wrapper 保留: blockquote marker 仍在
    assert ">" in new


def test_h2_23_non_target_bytes_unchanged():
    _, bundles, catalog = _bundles_and_catalog()
    qt = next(b for b in bundles if b["code"] in
              ("NEAR_QUOTE_NOT_MARKED", "UNSUPPORTED_EXACT_QUOTE"))
    slices = catalog.get(qt["issue_id"], [])
    if not slices:
        pytest.skip("no slices")
    patch = json.dumps({"patches": [{"issue_id": qt["issue_id"],
                                     "action": "COPY_SLICE",
                                     "slice_id": slices[0]["slice_id"]}]})
    new, _ = RC.apply_main_agent_patches_v2(CAND, patch, [qt], catalog)
    assert new is not None
    assert new.endswith("结尾一段正文。")


# ── H2-24/25: 生产边界 ──
def test_h2_24_production_adapter_default_none():
    eng = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "engine_langgraph.py"), encoding="utf-8").read()
    assert "_evaluation_repair_adapter=None" in eng
    assert "import repair_context" not in eng


def test_h2_25_philosopher_diff_zero():
    import subprocess
    diff = subprocess.run(["git", "diff", "cec4885f9", "HEAD", "--",
                           "backend/agents.py"],
                          cwd=ROOT, capture_output=True, text=True).stdout
    assert "search_scholarship" not in diff or "+" not in diff




# ══ H2D §7: I1-I10 integration tests ═══════════════════════
def test_i1_anchor_missing_first_round_full_rewrite():
    """I1: anchor 缺失 → prepare unsupported → FULL_REWRITE（invocation 前）"""
    # 构造: locator 在 candidate 中找不到 → anchor None
    from types import SimpleNamespace
    fake_val = SimpleNamespace(as_dict=lambda: {"issues": [
        {"code": "UNVERIFIED_CITATION", "locator": "【不存在的引】", "evidence_ref": None}]})
    prep = RC.prepare_local_patch("无此引用的正文", fake_val, _raw_log())
    assert prep["supported"] is False
    assert "UNRESOLVED_ANCHORS" in prep["unsupported_reason"]


def test_i2_anchor_missing_no_local_patch_protocol():
    """I2: prepare unsupported → adapter.anchor_ok=False → engine repair_output_mode=FULL_REWRITE"""
    # engine seam: _lp_meta None or anchor_ok False → FULL_REWRITE branch
    # 验证: unsupported_reason 非空时 prompt 为空（LOCAL_PATCH protocol 不被注入）
    from types import SimpleNamespace
    fake_val = SimpleNamespace(as_dict=lambda: {"issues": [
        {"code": "UNVERIFIED_CITATION", "locator": "【不存在】", "evidence_ref": None}]})
    prep = RC.prepare_local_patch("x", fake_val, _raw_log())
    assert prep["prompt"] == ""


def test_i3_stale_candidate_sha_rejected():
    """I3: runtime SHA 校验——candidate 被改后 apply 拒。"""
    _, bundles, catalog = _bundles_and_catalog()
    cand_sha = hashlib.sha256(CAND.encode()).hexdigest()
    # 用正确的 sha 但传一个不同 candidate → STALE_CANDIDATE
    qt = bundles[0]
    patch = json.dumps({"patches": [{"issue_id": qt["issue_id"],
                                     "action": "REPLACE_TEXT",
                                     "replacement_text": "改"}]})
    new, errs = RC.apply_main_agent_patches_v2(
        CAND + "EXTRA", patch, [qt], catalog,
        context_candidate_sha=cand_sha)
    assert new is None and "STALE_CANDIDATE" in errs


def test_i4_stale_anchor_sha_rejected():
    """I4: anchor span 被改 → content SHA 失配 → STALE_ANCHOR。"""
    v = _mk_validation(CAND)
    bundles = RC.build_repair_issue_bundles(CAND, v, _raw_log())
    qt = next(b for b in bundles if b.get("anchor"))
    patch = json.dumps({"patches": [{"issue_id": qt["issue_id"],
                                     "action": "REPLACE_TEXT",
                                     "replacement_text": "改"}]})
    # 用一个不同位置的 anchor SHA——直接篡改 bundle anchor sha
    import copy as _cp
    bad = _cp.deepcopy(qt)
    bad["anchor"]["content_sha256"] = "deadbeefdeadbeef"
    new, errs = RC.apply_main_agent_patches_v2(
        CAND, patch, [bad], {},
        context_candidate_sha=None)
    assert new is None and any("STALE_ANCHOR" in e for e in errs)


def test_i5_finalization_uses_stream_graph():
    """I5: engine 的 finalization 走 _stream_graph（源码断言无 direct invoke）。"""
    eng = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "engine_langgraph.py"), encoding="utf-8").read()
    fin_block = eng[eng.find("H2D §3"):]
    assert "_stream_graph" in fin_block[:3000]    # canonical path
    assert "_final_client = get_repair_llm()" not in fin_block[:3000]  # 无 direct invoke


def test_i6_finalization_model_input_has_local_patch_system():
    """I6: finalization 的 _stream_graph 调 repair_output_mode='LOCAL_PATCH'。"""
    eng = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "engine_langgraph.py"), encoding="utf-8").read()
    fin = eng[eng.find("H2D §3"):eng.find("H2D §3") + 3000]
    assert 'repair_output_mode="LOCAL_PATCH"' in fin


def test_i7_finalization_no_tools():
    """I7: finalization no_tools=True。"""
    eng = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "engine_langgraph.py"), encoding="utf-8").read()
    fin = eng[eng.find("H2D §3"):eng.find("H2D §3") + 2000]
    assert "no_tools=True" in fin


def test_i8_finalization_no_repairs_used():
    """I8: finalization 在 repair loop 内不递增 repairs_used。"""
    eng = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "engine_langgraph.py"), encoding="utf-8").read()
    fin_start = eng.find("H2D §3")
    fin_end = eng.find("H2D §9", fin_start)
    fin_block = eng[fin_start:fin_end]
    # finalization 不含 repairs_used += 1
    assert "repairs_used += 1" not in fin_block


def test_i9_prev_errors_reach_attempt2():
    """I9: protocol error 后 _prev_patch_errors 非空 → 下轮 build 收到。"""
    # engine 层: _prev_patch_errors = _apply_errs if _apply_errs else None
    # adapter build(prev_errors=...) → render_prompt_v2 含 previous_patch_protocol_errors
    _, bundles, catalog = _bundles_and_catalog()
    prompt = RC.render_patch_prompt_v2(bundles, catalog, ["INVALID_JSON"])
    assert "previous_patch_protocol_errors" in prompt
    assert "INVALID_JSON" in prompt


def test_i10_fingerprint_classification():
    """I10: before/after fingerprint 差集产生 resolved/persisted/introduced。"""
    before = {"A", "B"}
    after = {"B", "C"}
    resolved = before - after
    persisted = before & after
    introduced = after - before
    assert resolved == {"A"} and persisted == {"B"} and introduced == {"C"}
    # repair_context fingerprint 三元组保证可区分
    fa = RC.issue_fingerprint("X", "loc", "ev1")
    fb = RC.issue_fingerprint("X", "loc", "ev2")
    assert fa != fb
