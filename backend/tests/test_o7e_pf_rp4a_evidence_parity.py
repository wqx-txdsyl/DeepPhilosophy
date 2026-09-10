# -*- coding: utf-8 -*-
"""O7-E PF-RP4A Judge Evidence Parity: M1-M5 回归（真实 SCHOL_CAL2 artifact）。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import quote_bound as QB

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools", "evaluation"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import o7e_bakeoff_judge2 as J2
from tools_final_gate_helper import check_final_gate

_ART = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "docs/evidence/o7e_calib_SCHOL_CAL2.json")


def _case(cid):
    runs = json.load(open(_ART, encoding="utf-8"))
    return next(r for r in runs if r["case_id"] == cid)


def _joined_windows(r):
    windows, _meta = J2._replay_windows(r)
    return "".join(w["source_window"] for w in windows), windows


def test_m1_h13_heidegger_sentence_replayed():
    h13 = _case("H13")
    assert "c5013f33fe01#4" in ((h13.get("evidence_digest") or {})
                                .get("facts", {}).get("read_chapters") or [])
    joined, _w = _joined_windows(h13)
    assert "无世界的单纯主体" in joined, "H13 被judge指控伪造的句子必须出现在 replay 中"


def test_m2_h07_locke_sentence_replayed():
    h07 = _case("H07")
    assert "44a32441dabe#31" in ((h07.get("evidence_digest") or {})
                                 .get("facts", {}).get("read_chapters") or [])
    joined, _w = _joined_windows(h07)
    assert "組織适当的身体" in joined, "H07 被judge判 FALSE_EXACT_QUOTE 的原句必须在 replay 中"


def test_m3_scare_quotes_never_crowd_out_textual_claims():
    """候选=全部 quote spans + substantial claims; 截断只发生在全量排序之后,
    且 top-K 上限 24——前 12 个 scare quotes 不能挤掉后面的长 textual claim。"""
    h13 = _case("H13")
    windows, meta = J2._replay_windows(h13)
    assert meta["primary_replay_candidates"] > 12          # 候选远多于旧 [:12]
    assert len(windows) <= 24                              # bounded top-K
    # 排序性质: windows 的 overlap 单调不增
    ovs = [w["overlap"] for w in windows]
    assert ovs == sorted(ovs, reverse=True)
    assert meta["primary_replay_coverage_rate"] > 0


def test_m4_replay_sources_subset_of_recorded_chapters():
    for cid in ("H13", "H07", "H04", "S4", "S7", "H02", "H03"):
        r = _case(cid)
        windows, meta = J2._replay_windows(r)
        recorded = set((r.get("evidence_digest") or {})
                       .get("facts", {}).get("read_chapters") or [])
        assert all(w["chapter_key"] in recorded for w in windows), cid
        assert meta["new_primary_source_ids"] == 0         # M5


def test_m5_compact_digest_structured_not_blind_truncated():
    d = J2._compact_digest(_case("H13"))
    assert isinstance(d, dict) and "used_evidence" in d
    assert isinstance(d["used_evidence"], list)


# ── PF-RP4B-R1: o7e_final_gate 机械回归（artifact=2 → 无论回执写什么必须 FAIL）──
def test_final_gate_v3_summary_fails_on_median_lt2():
    import pytest
    from tools_final_gate_helper import load_v3_summary, check_final_gate
    try:
        summary = load_v3_summary()
    except FileNotFoundError:
        pytest.skip("V3 summary 未归档")
    assert summary["REQUIRED_DIMENSION_MEDIAN_LT_2"] == 2   # canonical 真值
    result = check_final_gate(summary)
    assert result["DELIVERY_GATE"] == "PASS"
    assert result["SCHOLARLY_GATE"] == "FAIL"
    assert result["FAILED_GATES"] == ["REQUIRED_DIMENSION_MEDIAN_LT_2"]
    assert result["FINAL_VERDICT"] == "V3_SCHOLARLY_GATE_NOT_MET"


def test_final_gate_pass_path():
    summary = {
        "FINAL_PUBLICATION_RATE": 1.0, "TERMINAL_PENDING": 0,
        "TOOL_LOOP_ABORTS": 0, "UNVERIFIED_PUBLIC_EXACT_QUOTES": 0,
        "STITCHED_PUBLIC_QUOTES": 0, "PUBLIC_INVALID_CITATIONS": 0,
        "VALIDATOR_EMPTY_FINAL": 0, "TERMINAL_CANDIDATE_EMPTY": 0,
        "REPAIR_CREATES_NEW_FATAL_ERROR": 0,
        "LOCAL_PATCH_ANCHOR_RESOLUTION_RATE": 1.0, "PROMPT_ISSUE_COVERAGE": 1.0,
        "LINKED_EVIDENCE_STARVATION": 0, "UNKNOWN_SLICE_ID": 0,
        "UNINTENTIONAL_QUOTE_WRAPPER_LOSS": 0, "NON_TARGET_TEXT_CHANGED_CHARS": 0,
        "APPLICABLE_DIMENSION_MEAN": 3.5,
        "required_dims": {"textual_grounding": 3.6,
                          "argument_reconstruction": 3.5,
                          "interpretive_plurality": 3.2,
                          "historical_discipline": 3.5,
                          "literature_orientation": 3.3},
        "REQUIRED_DIMENSION_MEDIAN_LT_2": 0,
        "REQUIRED_DIMENSION_MISSING_SCORE": 0,
        "JUDGE_CASES_EXPECTED": 8, "JUDGE_CASES_VALID": 8,
        "JUDGE_CASES_MISSING": 0, "EVALUATION_INVALID": False,
        "FATAL_FLAG_COUNTS_BY_TYPE": {f: 0 for f in (
            "FABRICATED_BIBLIOGRAPHY", "FABRICATED_SCHOLAR_ATTRIBUTION",
            "PRIMARY_TEXT_MISREPRESENTATION", "MAJOR_ANACHRONISM",
            "FALSE_EXACT_QUOTE", "LITERATURE_ACCESS_OVERCLAIM")},
    }
    result = check_final_gate(summary)
    assert result["DELIVERY_GATE"] == "PASS"
    assert result["SCHOLARLY_GATE"] == "PASS"
    assert result["FAILED_GATES"] == []
    assert result["FINAL_VERDICT"] == "PASS"


# ── V3-RP2 §0: final-gate fail-close（缺字段 ≠ 通过）──
def test_final_gate_fail_closed_on_missing_fields():
    base_pass = {
        "FINAL_PUBLICATION_RATE": 1.0, "TERMINAL_PENDING": 0,
        "TOOL_LOOP_ABORTS": 0, "UNVERIFIED_PUBLIC_EXACT_QUOTES": 0,
        "STITCHED_PUBLIC_QUOTES": 0, "PUBLIC_INVALID_CITATIONS": 0,
        "VALIDATOR_EMPTY_FINAL": 0, "TERMINAL_CANDIDATE_EMPTY": 0,
        "REPAIR_CREATES_NEW_FATAL_ERROR": 0,
        "LOCAL_PATCH_ANCHOR_RESOLUTION_RATE": 1.0, "PROMPT_ISSUE_COVERAGE": 1.0,
        "LINKED_EVIDENCE_STARVATION": 0, "UNKNOWN_SLICE_ID": 0,
        "UNINTENTIONAL_QUOTE_WRAPPER_LOSS": 0, "NON_TARGET_TEXT_CHANGED_CHARS": 0,
        "APPLICABLE_DIMENSION_MEAN": 3.5,
        "required_dims": {"textual_grounding": 3.6,
                          "argument_reconstruction": 3.5,
                          "interpretive_plurality": 3.2,
                          "historical_discipline": 3.5,
                          "literature_orientation": 3.3},
        "REQUIRED_DIMENSION_MEDIAN_LT_2": 0,
        "REQUIRED_DIMENSION_MISSING_SCORE": 0,
        "JUDGE_CASES_EXPECTED": 8, "JUDGE_CASES_VALID": 8, "JUDGE_CASES_MISSING": 0,
        "EVALUATION_INVALID": False,
        "FATAL_FLAG_COUNTS_BY_TYPE": {f: 0 for f in (
            "FABRICATED_BIBLIOGRAPHY", "FABRICATED_SCHOLAR_ATTRIBUTION",
            "PRIMARY_TEXT_MISREPRESENTATION", "MAJOR_ANACHRONISM",
            "FALSE_EXACT_QUOTE", "LITERATURE_ACCESS_OVERCLAIM")},
    }
    # a) 缺 MEDIAN_LT_2 → FAIL（不得当 0 通过）
    s = dict(base_pass); s.pop("REQUIRED_DIMENSION_MEDIAN_LT_2")
    assert check_final_gate(s)["FAILED_GATES"]  # fail-close: 缺失即 FAIL
    # b) 缺一个 fatal key → FAIL
    s2 = dict(base_pass)
    s2["FATAL_FLAG_COUNTS_BY_TYPE"] = {k: v for k, v in
                                       base_pass["FATAL_FLAG_COUNTS_BY_TYPE"].items()
                                       if k != "FALSE_EXACT_QUOTE"}
    assert check_final_gate(s2)["FAILED_GATES"]
    # c) EVALUATION_INVALID=true → FAIL
    s3 = dict(base_pass); s3["EVALUATION_INVALID"] = True
    assert check_final_gate(s3)["FAILED_GATES"]
    # d) JUDGE_CASES_MISSING=1 → FAIL
    s4 = dict(base_pass); s4["JUDGE_CASES_MISSING"] = 1
    assert check_final_gate(s4)["FAILED_GATES"]
    # 完整字段 → PASS
    assert check_final_gate(dict(base_pass))["FAILED_GATES"] == []
