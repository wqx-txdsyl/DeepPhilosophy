# -*- coding: utf-8 -*-
"""O7-E V3-RP1: 机械 final-gate check——只读 summary, 零语义判断。

按冻结阈值机械输出 DELIVERY_GATE / SCHOLARLY_GATE / FINAL_VERDICT /
FAILED_GATES[]。存在目的: 防止「artifact=2、receipt=0」类结论层读错再发
（canonical summary 是唯一真值, commit message / receipt 不构成证据）。
"""
import json
import sys

THRESHOLDS = {
    "FINAL_PUBLICATION_RATE_MIN": 0.90,
    "TERMINAL_PENDING": 0,
    "TOOL_LOOP_ABORTS": 0,
    "UNVERIFIED_PUBLIC_EXACT_QUOTES": 0,
    "STITCHED_PUBLIC_QUOTES": 0,
    "PUBLIC_INVALID_CITATIONS": 0,
    "VALIDATOR_EMPTY_FINAL": 0,
    "TERMINAL_CANDIDATE_EMPTY": 0,
    "REPAIR_CREATES_NEW_FATAL_ERROR": 0,
    "LOCAL_PATCH_ANCHOR_RESOLUTION_RATE": 1.0,
    "PROMPT_ISSUE_COVERAGE": 1.0,
    "LINKED_EVIDENCE_STARVATION": 0,
    "UNKNOWN_SLICE_ID": 0,
    "UNINTENTIONAL_QUOTE_WRAPPER_LOSS": 0,
    "NON_TARGET_TEXT_CHANGED_CHARS": 0,
    "APPLICABLE_DIMENSION_MEAN_MIN": 3.20,
    "TEXTUAL_GROUNDING_REQUIRED_MEAN_MIN": 3.40,
    "ARGUMENT_RECONSTRUCTION_REQUIRED_MEAN_MIN": 3.20,
    "INTERPRETIVE_PLURALITY_REQUIRED_MEAN_MIN": 3.00,
    "HISTORICAL_DISCIPLINE_REQUIRED_MEAN_MIN": 3.40,
    "LITERATURE_ORIENTATION_REQUIRED_MEAN_MIN": 3.20,
    "REQUIRED_DIMENSION_MEDIAN_LT_2": 0,
    "REQUIRED_DIMENSION_MISSING_SCORE": 0,
}

FATAL_KEYS = ("FABRICATED_BIBLIOGRAPHY", "FABRICATED_SCHOLAR_ATTRIBUTION",
              "PRIMARY_TEXT_MISREPRESENTATION", "MAJOR_ANACHRONISM",
              "FALSE_EXACT_QUOTE", "LITERATURE_ACCESS_OVERCLAIM")

REQUIRED_DIM_MEANS = {
    "textual_grounding": ("TEXTUAL_GROUNDING_REQUIRED_MEAN_MIN", 3.40),
    "argument_reconstruction": ("ARGUMENT_RECONSTRUCTION_REQUIRED_MEAN_MIN", 3.20),
    "interpretive_plurality": ("INTERPRETIVE_PLURALITY_REQUIRED_MEAN_MIN", 3.00),
    "historical_discipline": ("HISTORICAL_DISCIPLINE_REQUIRED_MEAN_MIN", 3.40),
    "literature_orientation": ("LITERATURE_ORIENTATION_REQUIRED_MEAN_MIN", 3.20),
}


def check_final_gate(summary, case_count=None):
    """机械对照冻结阈值。summary = canonical judge/delivery summary dict。"""
    failed = []

    def _num(key):
        v = summary.get(key)
        return v if isinstance(v, (int, float)) else None

    # delivery
    pub_rate = _num("FINAL_PUBLICATION_RATE")
    if pub_rate is None:
        pub, comp = _num("CALIBRATION_PUBLISHED"), _num("CALIBRATION_COMPLETED")
        pub_rate = (pub / comp) if (pub is not None and comp) else None
    if pub_rate is None or pub_rate < THRESHOLDS["FINAL_PUBLICATION_RATE_MIN"]:
        failed.append("FINAL_PUBLICATION_RATE")
    for key in ("TERMINAL_PENDING", "TOOL_LOOP_ABORTS",
                "UNVERIFIED_PUBLIC_EXACT_QUOTES", "STITCHED_PUBLIC_QUOTES",
                "PUBLIC_INVALID_CITATIONS", "VALIDATOR_EMPTY_FINAL",
                "TERMINAL_CANDIDATE_EMPTY", "REPAIR_CREATES_NEW_FATAL_ERROR"):
        if (_num(key) or 0) != THRESHOLDS[key]:
            failed.append(key)
    for key in ("LOCAL_PATCH_ANCHOR_RESOLUTION_RATE", "PROMPT_ISSUE_COVERAGE"):
        v = _num(key)
        if v is None or v < THRESHOLDS[key]:
            failed.append(key)
    for key in ("LINKED_EVIDENCE_STARVATION", "UNKNOWN_SLICE_ID",
                "UNINTENTIONAL_QUOTE_WRAPPER_LOSS",
                "NON_TARGET_TEXT_CHANGED_CHARS"):
        if (_num(key) or 0) != 0:
            failed.append(key)

    # scholarly
    amean = _num("APPLICABLE_DIMENSION_MEAN")
    if amean is None:
        amean = _num("applicable_mean")   # judge summary 的键名（canonical）
    if amean is None or amean < THRESHOLDS["APPLICABLE_DIMENSION_MEAN_MIN"]:
        failed.append("APPLICABLE_DIMENSION_MEAN")
    req_dims = summary.get("required_dims") or summary.get("required_dims_mean") or {}
    for dim, (thr_key, thr) in REQUIRED_DIM_MEANS.items():
        v = req_dims.get(dim)
        if not isinstance(v, (int, float)) or v < THRESHOLDS[thr_key]:
            failed.append(thr_key)
    med_lt2 = _num("REQUIRED_DIMENSION_MEDIAN_LT_2")
    if med_lt2 is None or med_lt2 != 0:
        failed.append("REQUIRED_DIMENSION_MEDIAN_LT_2")     # 缺失也算 FAIL（fail-close）
    miss_score = _num("REQUIRED_DIMENSION_MISSING_SCORE")
    if miss_score is None or miss_score != 0:
        failed.append("REQUIRED_DIMENSION_MISSING_SCORE")
    # PF-RP5-F1 §0 fail-close: 缺字段 ≠ 通过
    fatal_counts = summary.get("FATAL_FLAG_COUNTS_BY_TYPE") or {}
    for f in FATAL_KEYS:
        if f not in fatal_counts or (fatal_counts.get(f) or 0) != 0:
            failed.append(f)
    # scholarly 记账完整性强制（judge summary 四要素缺一即 FAIL）
    jc_expected = _num("JUDGE_CASES_EXPECTED")
    jc_valid = _num("JUDGE_CASES_VALID")
    jc_missing = _num("JUDGE_CASES_MISSING")
    eval_invalid = summary.get("EVALUATION_INVALID")
    if jc_expected is None or jc_valid is None or jc_missing is None:
        failed.append("JUDGE_CASE_ACCOUNTING_MISSING")
    elif jc_valid != jc_expected or jc_missing != 0:
        failed.append("JUDGE_CASES_MISSING")
    if eval_invalid is not False:
        failed.append("EVALUATION_INVALID")

    delivery_pass = not [g for g in failed if g in (
        "FINAL_PUBLICATION_RATE", "TERMINAL_PENDING", "TOOL_LOOP_ABORTS",
        "UNVERIFIED_PUBLIC_EXACT_QUOTES", "STITCHED_PUBLIC_QUOTES",
        "PUBLIC_INVALID_CITATIONS", "VALIDATOR_EMPTY_FINAL",
        "TERMINAL_CANDIDATE_EMPTY", "REPAIR_CREATES_NEW_FATAL_ERROR",
        "LOCAL_PATCH_ANCHOR_RESOLUTION_RATE", "PROMPT_ISSUE_COVERAGE",
        "LINKED_EVIDENCE_STARVATION", "UNKNOWN_SLICE_ID",
        "UNINTENTIONAL_QUOTE_WRAPPER_LOSS", "NON_TARGET_TEXT_CHANGED_CHARS")]
    scholarly_fail = [g for g in failed if g not in (
        "FINAL_PUBLICATION_RATE", "TERMINAL_PENDING", "TOOL_LOOP_ABORTS",
        "UNVERIFIED_PUBLIC_EXACT_QUOTES", "STITCHED_PUBLIC_QUOTES",
        "PUBLIC_INVALID_CITATIONS", "VALIDATOR_EMPTY_FINAL",
        "TERMINAL_CANDIDATE_EMPTY", "REPAIR_CREATES_NEW_FATAL_ERROR",
        "LOCAL_PATCH_ANCHOR_RESOLUTION_RATE", "PROMPT_ISSUE_COVERAGE",
        "LINKED_EVIDENCE_STARVATION", "UNKNOWN_SLICE_ID",
        "UNINTENTIONAL_QUOTE_WRAPPER_LOSS", "NON_TARGET_TEXT_CHANGED_CHARS")]
    return {"DELIVERY_GATE": "PASS" if delivery_pass else "FAIL",
            "SCHOLARLY_GATE": "FAIL" if scholarly_fail else "PASS",
            "FAILED_GATES": sorted(set(failed)),
            "FINAL_VERDICT": ("PASS" if not failed else
                              ("V3_DELIVERY_GATE_NOT_MET" if not delivery_pass
                               else "V3_SCHOLARLY_GATE_NOT_MET"))}


def main(summary_path):
    summary = json.load(open(summary_path, encoding="utf-8"))
    print(json.dumps(check_final_gate(summary), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
