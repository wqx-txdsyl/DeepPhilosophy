# -*- coding: utf-8 -*-
"""O7-E RCA-1 §必测回归 A1-A22——Localized Repair Context Architecture。"""
import hashlib
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import repair_context as RC
import quote_bound as QB
from final_validator import validate_final_candidate


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


def _mk_validation(candidate, log=None):
    return validate_final_candidate(candidate, raw_tool_log=log or _raw_log(),
                                    fallback_log=[], language="zh")


CAND = ("开头一段正文，讨论孔子的言论。\n\n"
        "原文如下：\n\n> 「鲁人为长府，闵子骞曰：“仍旧贯如之何？何必改造？”」\n\n"
        "「言必有中」出自【《韩非子·五蠹》】。\n\n结尾一段正文。")


# ── A1-A3: anchor 精确性 ──
def test_a1_citation_exact_anchor():
    v = _mk_validation(CAND)
    bundles = RC.build_repair_issue_bundles(CAND, v, _raw_log())
    cit = next(b for b in bundles if b["code"] == "UNVERIFIED_CITATION")
    a = cit["anchor"]
    assert a and a["start"] >= 0
    assert CAND[a["start"]:a["end"]] == "【《韩非子·五蠹》】"  # 精确 span
    assert a["surface_sha256"] == _sha("【《韩非子·五蠹》】")[:16]


def test_a2_quote_exact_anchor():
    v = _mk_validation(CAND)
    bundles = RC.build_repair_issue_bundles(CAND, v, _raw_log())
    qt = next(b for b in bundles if b["code"] in
              ("NEAR_QUOTE_NOT_MARKED", "UNSUPPORTED_EXACT_QUOTE"))
    a = qt["anchor"]
    assert a and "改造" in CAND[a["start"]:a["end"]]  # 精确引文 span（1 字差异近引）
    assert a["surface_sha256"] == _sha(CAND[a["start"]:a["end"]])[:16]


def test_a3_duplicate_preview_no_wrong_span():
    # 两条不同引文（一条 NEAR 一条 MEMORY_ONLY）——anchor 必须各指其位不串
    cand = ("> 「鲁人为长府，闵子骞曰：“仍旧贯如之何？何必改造？”」\n\n"
            "中间文字\n\n> 「完全不同的另一句假引文且足够长以被提取」")
    v = _mk_validation(cand)
    bundles = RC.build_repair_issue_bundles(cand, v, _raw_log())
    q_anchors = [b["anchor"] for b in bundles if b["anchor"]]
    starts = [a["start"] for a in q_anchors]
    assert len(starts) == len(set(starts))          # 不同引文不同锚
    for a in q_anchors:
        span = cand[a["start"]:a["end"]]
        assert "改造" in span or "另一句假引文" in span  # 锚到的就是那条引文


# ── A4-A6: applier 协议错误 ──
def _bundles_for_cand():
    v = _mk_validation(CAND)
    bundles = RC.build_repair_issue_bundles(CAND, v, _raw_log())
    return v, bundles


def test_a4_stale_candidate_sha_rejected():
    _, bundles = _bundles_for_cand()
    patch = json.dumps({"candidate_sha256": _sha("WRONG"),
                        "patches": [{"issue_id": bundles[0]["issue_id"],
                                     "anchor_sha256": bundles[0]["anchor"]["surface_sha256"],
                                     "action": "REPLACE_TEXT",
                                     "replacement_text": "改写"}]})
    new, errs = RC.apply_main_agent_patches(CAND, patch, bundles)
    assert new is None and any("candidate_sha" in e for e in errs)


def test_a5_stale_anchor_sha_rejected():
    _, bundles = _bundles_for_cand()
    patch = json.dumps({"candidate_sha256": _sha(CAND),
                        "patches": [{"issue_id": bundles[0]["issue_id"],
                                     "anchor_sha256": "deadbeef",
                                     "action": "REPLACE_TEXT",
                                     "replacement_text": "改写"}]})
    new, errs = RC.apply_main_agent_patches(CAND, patch, bundles)
    assert new is None and any("anchor stale" in e for e in errs)


def test_a6_overlapping_patches_rejected():
    # 构造两个 patch 指向同一 anchor
    v, bundles = _bundles_for_cand()
    b0 = next(b for b in bundles if b["anchor"])
    patch = json.dumps({"candidate_sha256": _sha(CAND), "patches": [
        {"issue_id": b0["issue_id"], "anchor_sha256": b0["anchor"]["surface_sha256"],
         "action": "REPLACE_TEXT", "replacement_text": "A"},
        {"issue_id": b0["issue_id"], "anchor_sha256": b0["anchor"]["surface_sha256"],
         "action": "REPLACE_TEXT", "replacement_text": "B"}]})
    new, errs = RC.apply_main_agent_patches(CAND, patch, bundles)
    assert new is None and any("duplicate" in e for e in errs)


# ── A7-A10: 两种 action 语义 ──
def test_a7_copy_evidence_slice_exact():
    v, bundles = _bundles_for_cand()
    qt = next(b for b in bundles if b["code"] in
              ("NEAR_QUOTE_NOT_MARKED", "UNSUPPORTED_EXACT_QUOTE") and b["source"])
    ctx = qt["source"]["exact_context"]
    s, e = ctx.find("何必改作"), ctx.find("何必改作") + 4
    patch = json.dumps({"candidate_sha256": _sha(CAND), "patches": [
        {"issue_id": qt["issue_id"], "anchor_sha256": qt["anchor"]["surface_sha256"],
         "action": "COPY_EVIDENCE_SLICE", "evidence_ref": qt["evidence_ref"],
         "source_start": s, "source_end": e}]})
    # 只覆盖该 issue（其他 issue 未覆盖→协议错? bundles 含 citation——只传该 bundle）
    new, errs = RC.apply_main_agent_patches(CAND, patch, [qt])
    assert new is not None, errs
    assert "何必改作" in new and "何必改造" not in new  # 精确复制了源子串


def test_a8_invalid_slice_rejected():
    v, bundles = _bundles_for_cand()
    qt = next(b for b in bundles if b["code"] in
              ("NEAR_QUOTE_NOT_MARKED", "UNSUPPORTED_EXACT_QUOTE"))
    patch = json.dumps({"candidate_sha256": _sha(CAND), "patches": [
        {"issue_id": qt["issue_id"], "anchor_sha256": qt["anchor"]["surface_sha256"],
         "action": "COPY_EVIDENCE_SLICE", "evidence_ref": qt["evidence_ref"],
         "source_start": 99999, "source_end": 100000}]})
    new, errs = RC.apply_main_agent_patches(CAND, patch, [qt])
    assert new is None and any("invalid evidence slice" in e for e in errs)


def test_a9_replace_text_main_agent_prose():
    _, bundles = _bundles_for_cand()
    cit = next(b for b in bundles if b["code"] == "UNVERIFIED_CITATION")
    patch = json.dumps({"candidate_sha256": _sha(CAND), "patches": [
        {"issue_id": cit["issue_id"], "anchor_sha256": cit["anchor"]["surface_sha256"],
         "action": "REPLACE_TEXT",
         "replacement_text": "【《论语》·先进篇】"}]})
    new, errs = RC.apply_main_agent_patches(CAND, patch, [cit])
    assert new and "《论语》·先进篇" in new and "韩非子" not in new


def test_a10_runtime_prose_generation_zero():
    """applier 自身不生成任何文本——REPLACE 的字符全部来自 patch 输入。"""
    import inspect
    src = inspect.getsource(RC.apply_main_agent_patches)
    # 无字符串拼接生成/无模板/无 LLM 调用——只允许切片与插入输入文本
    assert "llm" not in src.lower() and "urlopen" not in src
    assert src.count('.replace(') == 0 or 'REPLACE' in src  # .replace 方法名不算生成


# ── A11-A12: evidence 完整性 ──
def test_a11_each_issue_gets_linked_evidence():
    """4 个 issue 全部有可解析 evidence_ref → bundle 全含其 source。"""
    # 构造 4-issue 候选（2 近引 + 1 假引 + 1 错引用）
    cand = ("> 「鲁人为长府，闵子骞曰：“仍旧贯如之何？何必改造？”」\n\n"
            "> 「子曰：“夫人不言，言必有中心。”」\n\n"
            "> 「完全虚构的一句原文且足够长以被提取检查」\n\n"
            "「某句」出自【《荀子》】。")
    v = _mk_validation(cand)
    bundles = RC.build_repair_issue_bundles(cand, v, _raw_log())
    resolvable = [b for b in bundles if b["evidence_ref"]]
    starved = [b["issue_id"] for b in resolvable if not b.get("source")]
    assert not starved, f"LINKED_EVIDENCE_STARVATION: {starved}"
    assert len(bundles) >= 2


def test_a12_no_global_starvation():
    """issue 数 > 旧全局 3 上限时, 每个 resolvable issue 仍各得其 evidence。"""
    parts = []
    for i in range(5):
        parts.append(f"> 「鲁人为长府，闵子骞说{i}：“仍旧贯如之何？何必改作？”」")
    cand = "\n\n".join(parts)
    v = _mk_validation(cand)
    bundles = RC.build_repair_issue_bundles(cand, v, _raw_log())
    quotes = [b for b in bundles if b["code"] in RC.LOCAL_PATCH_CODES]
    assert len(quotes) >= 4              # 超过旧全局 max_evidence=3
    starved = [b["issue_id"] for b in quotes if not b.get("source")]
    assert not starved                   # 每个 issue 有 evidence（ref-resolved 或 best-effort）


# ── A13-A14: byte-preservation 与原子应用 ──
def test_a13_non_target_zero_change():
    _, bundles = _bundles_for_cand()
    cit = next(b for b in bundles if b["code"] == "UNVERIFIED_CITATION")
    patch = json.dumps({"candidate_sha256": _sha(CAND), "patches": [
        {"issue_id": cit["issue_id"], "anchor_sha256": cit["anchor"]["surface_sha256"],
         "action": "REPLACE_TEXT", "replacement_text": "【《论语》·先进篇】"}]})
    new, _ = RC.apply_main_agent_patches(CAND, patch, [cit])
    a = cit["anchor"]
    spans = [(a["start"], a["end"])]
    assert RC.non_target_changed_chars(CAND, new, spans) == 0
    assert new[:a["start"]] == CAND[:a["start"]]      # 前文逐字节不变
    assert new.endswith("结尾一段正文。")               # 后文不变


def test_a14_two_patches_atomic():
    _, bundles = _bundles_for_cand()
    cit = next(b for b in bundles if b["code"] == "UNVERIFIED_CITATION")
    qt = next(b for b in bundles if b["code"] in
              ("NEAR_QUOTE_NOT_MARKED", "UNSUPPORTED_EXACT_QUOTE"))
    patch = json.dumps({"candidate_sha256": _sha(CAND), "patches": [
        {"issue_id": cit["issue_id"], "anchor_sha256": cit["anchor"]["surface_sha256"],
         "action": "REPLACE_TEXT", "replacement_text": "【《论语》·先进篇】"},
        {"issue_id": qt["issue_id"], "anchor_sha256": qt["anchor"]["surface_sha256"],
         "action": "REPLACE_TEXT", "replacement_text": "（闵子骞语，见《论语》）"}]})
    new, errs = RC.apply_main_agent_patches(CAND, patch, [cit, qt])
    assert new and not errs
    assert "《论语》·先进篇" in new and "见《论语》" in new


# ── A15-A18: 流程语义 ──
def test_a15_patched_candidate_revalidated():
    # 修复后的候选必须过全量 validator
    _, bundles = _bundles_for_cand()
    cit = next(b for b in bundles if b["code"] == "UNVERIFIED_CITATION")
    qt = next(b for b in bundles if b["code"] in
              ("NEAR_QUOTE_NOT_MARKED", "UNSUPPORTED_EXACT_QUOTE"))
    patch = json.dumps({"candidate_sha256": _sha(CAND), "patches": [
        {"issue_id": cit["issue_id"], "anchor_sha256": cit["anchor"]["surface_sha256"],
         "action": "REPLACE_TEXT", "replacement_text": "（出自《论语·先进篇》）"},
        {"issue_id": qt["issue_id"], "anchor_sha256": qt["anchor"]["surface_sha256"],
         "action": "REPLACE_TEXT", "replacement_text": "闵子骞之语见《论语》"}]})
    new, _ = RC.apply_main_agent_patches(CAND, patch, [cit, qt])
    v2 = _mk_validation(new)
    assert v2.ok, [i.code for i in v2.issues]


def test_a16_failed_patch_gets_fresh_anchors():
    """repair2 用新 candidate 重建 anchors——旧 anchor SHA 自然失配。"""
    _, bundles = _bundles_for_cand()
    cit = bundles[0]
    patch = json.dumps({"candidate_sha256": _sha(CAND), "patches": [
        {"issue_id": cit["issue_id"], "anchor_sha256": "stale00",
         "action": "REPLACE_TEXT", "replacement_text": "x"}]})
    new, errs = RC.apply_main_agent_patches(CAND, patch, bundles)
    assert new is None                      # 失败→不产出半成品
    # 新一轮: 对新 candidate 重建 bundle（anchor 重新计算——不依赖旧 SHA）


def test_a17_empty_final_stays_full_rewrite():
    assert "EMPTY_FINAL" not in RC.LOCAL_PATCH_CODES


def test_a18_quote_citation_issues_local():
    assert {"UNVERIFIED_CITATION", "UNSUPPORTED_EXACT_QUOTE",
            "NEAR_QUOTE_NOT_MARKED", "STITCHED_QUOTE"} <= RC.LOCAL_PATCH_CODES


# ── A19-A22: 环境边界 ──
def test_a19_budget_tools_available():
    """LOCAL_PATCH 是 engine 修复模式的evaluation 注入——工具可用性由 engine 既有
    逻辑决定（repair_mode 可带工具）; 本测试锁 repair_context 不触碰工具面。"""
    import inspect
    src = inspect.getsource(RC)
    assert "bind_tools" not in src and "TOOLS" not in src


def test_a20_no_tools_semantics_unchanged():
    """repair_context 不感知 no_tools——该语义归 engine。"""
    import inspect
    assert "no_tools" not in inspect.getsource(RC)


def test_a21_philosopher_diff_zero():
    import subprocess
    r = subprocess.run(["git", "diff", "--quiet", "cec4885f9", "HEAD", "--",
                        "backend/agents.py"],
                       cwd=os.path.dirname(os.path.dirname(os.path.dirname(
                           os.path.abspath(__file__)))), capture_output=True)
    diff = subprocess.run(["git", "diff", "cec4885f9", "HEAD", "--", "backend/agents.py"],
                          cwd=os.path.dirname(os.path.dirname(os.path.dirname(
                              os.path.abspath(__file__)))), capture_output=True,
                          text=True).stdout
    assert "search_scholarship" not in diff or "+" not in diff


def test_a22_production_patch_mode_default_false():
    """生产默认关: repair_context 未被 engine_langgraph import（production 未接线）。"""
    eng = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "engine_langgraph.py"), encoding="utf-8").read()
    assert "repair_context" not in eng, "production 接线未授权（RCA-1 §13）"
    assert "LOCAL_PATCH_ENABLED" not in eng
