# -*- coding: utf-8 -*-
"""O7-A — Scholarly Contract & Evaluation Constitution（evaluation-only 测试 T1–T20）

约束: 本文件不调用外部 LLM（校准为冻结后 gate 运行, 见 o7_scholarly_judge --calibrate）;
judge 判定逻辑测试用注入 transport 的确定性 canned verdict。
生产零改动以 T18（无生产导入）/T19（对 BASE 零 diff）静态证明。
"""
import ast
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "tools", "evaluation"))

BASE_SHA = "302f7380a4146d78374887063b336c5aa7381ddd"
BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(BACKEND)
EVAL_DIR = os.path.join(BACKEND, "tools", "evaluation")

import o7_scholarly_judge as J
import o7_scholarly_cases as C


def _verdict(scores=None, applic=None, flags=None, confidence=0.9, ledger=None):
    scores = scores or {}
    applic = applic or {}
    dims = {}
    for d in J.DIMENSIONS:
        appl = applic.get(d, "REQUIRED")
        sc = None if appl == "NOT_APPLICABLE" else scores.get(d, 3)
        dims[d] = {"applicability": appl, "score": sc,
                   "rationale": f"rationale for {d}", "supporting_spans": [],
                   "missing_requirements": []}
    return {
        "dimensions": dims,
        "fatal_flags": {f: {"value": bool(flags and f in flags), "offending_spans": [],
                            "reason": "seeded" if (flags and f in flags) else "",
                            "evidence_refs": [], "confidence": 0.95}
                        for f in J.FATAL_FLAGS},
        "claim_ledger": ledger or [],
        "overall_scholarly_assessment": "ok",
        "judge_confidence": confidence,
    }


def _canned(verdict):
    return lambda _prompt: json.dumps(verdict, ensure_ascii=False)


# ── T1/T2 — rubric 维度 schema 与 N/A 聚合 ─────────────────────────
def test_t1_rubric_dimensions_schema():
    assert len(J.DIMENSIONS) == 5
    assert set(J.DIMENSIONS) == {"textual_grounding", "argument_reconstruction",
                                 "interpretive_plurality", "historical_discipline",
                                 "literature_orientation"}
    v = _verdict()
    errs = J.validate_verdict(v)
    assert errs == []
    assert sorted(J.dimension_scores(v)) == sorted([(d, 3) for d in J.DIMENSIONS])


def test_t2_na_dimension_excluded_from_mean():
    v = _verdict(scores={"textual_grounding": 4, "argument_reconstruction": 2},
                 applic={"interpretive_plurality": "NOT_APPLICABLE"})
    assert J.validate_verdict(v) == []
    # N/A 维不入均值: (4+2+3+3)/4 = 3.0, 不是把 N/A 当 0 的 2.4
    assert J.scholarly_mean(v) == 3.0
    bad = _verdict(applic={"interpretive_plurality": "NOT_APPLICABLE"})
    bad["dimensions"]["interpretive_plurality"]["score"] = 0
    assert any("score=null" in e for e in J.validate_verdict(bad))


# ── T3 — plurality 非万能模板（案例元数据 + N/A 不扣分语义）────────
def test_t3_plurality_not_universally_required():
    prof = C.CALIBRATION_CASES
    assert prof["C5"]["applicability"]["interpretive_plurality"] == "REQUIRED"
    assert prof["C8"]["applicability"]["interpretive_plurality"] == "NOT_APPLICABLE"
    assert prof["C3"]["applicability"]["interpretive_plurality"] == "NOT_APPLICABLE"
    # C8-good fixture 不列两派 → 无任何 flag; judge 侧由 N/A 语义保证不因缺学者扣分
    assert "interpretive_plurality" not in " ".join(prof["C8"]["known_pitfalls"])


# ── T4 — 致命 flag 与分数分离 ────────────────────────────────────
def test_t4_fatal_flags_independent_from_score():
    v = _verdict(scores={"textual_grounding": 4}, flags={"FABRICATED_BIBLIOGRAPHY"})
    assert J.validate_verdict(v) == []
    assert J.scholarly_mean(v) >= 3 and J.raised_fatal_flags(v) == ["FABRICATED_BIBLIOGRAPHY"]


# ── T5–T11 — 植入错误的 fixture 由 judge（canned）检出 + 校准门 ────
def _canned_by_expect(fixtures):
    """确定性 judge: 对每个 fixture 按 expect_flags 出 flag（模拟理想 judge）。"""
    def transport(prompt):
        # 从 prompt 中识别 fixture —— 用答案文本前 24 字作为 key 探针
        raise AssertionError("直接用 run_judge(inp, transport) 逐 fixture 注入")
    return transport


def test_t5_to_t10_seeded_fatal_fixtures_detected_and_gate_full_recall():
    fixtures = C.calibration_fixtures()
    expected = C.expected_fatal_flags()
    assert expected, "必须存在植入致命错误的 BAD fixtures"
    results = {}
    for fid, f in fixtures.items():
        flags = expected.get(fid, [])
        v = _verdict(flags=set(flags), confidence=0.9)
        verdict = J.run_judge(f["judge_input"], transport=_canned(v))
        results[fid] = verdict
        if flags:
            assert set(J.raised_fatal_flags(verdict)) == set(flags), fid
    gate = J.calibration_gate(
        {**results,
         "__good__": [k for k, f in fixtures.items() if f["tier"] == "GOOD"],
         "__mid__": [k for k, f in fixtures.items() if f["tier"] == "MID"],
         "__bad__": [k for k, f in fixtures.items() if f["tier"] == "BAD"]},
        expected)
    assert gate["expected_fatal_total"] == sum(len(v) for v in expected.values())
    assert gate["expected_fatal_detected"] == gate["expected_fatal_total"]
    assert gate["expected_fatal_recall"] == 1.0      # T5-T10: 全部植入 flag 可被检出
    assert gate["false_fatal_on_goodmid_count"] == 0  # GOOD/MID fixture 零误报


def test_t11_metadata_only_is_not_full_text_read():
    acc = C.ACCESS_FIXTURES
    # L1: metadata-only 却描述内部论证 → 必须可触发 F6（校准时由真实 judge 触发）
    assert acc["C6-L1-bad"]["expect_flags"] == ["LITERATURE_ACCESS_OVERCLAIM"]
    assert acc["C6-L2-good"]["expect_flags"] == []   # abstract 合规 → 不得触发
    assert acc["C6-L3-good"]["expect_flags"] == []   # full-text read → 不得触发
    # 访问级别枚举四态 & ledger 可表达
    assert J.ACCESS_LEVELS == ["METADATA_ONLY", "ABSTRACT_AVAILABLE",
                               "FULL_TEXT_AVAILABLE", "FULL_TEXT_READ"]


# ── T12/T13 — Claim Ledger schema 与无 runtime 动作 ───────────────
def test_t12_claim_ledger_schema():
    ok = {"claim_id": "c1", "claim_span": "……", "claim_type": "CONTESTED_INTERPRETATION",
          "support": "PARTIAL", "access_level": "METADATA_ONLY"}
    assert J.validate_ledger_entry(ok) == []
    bad = {"claim_id": "", "claim_type": "MADE_UP", "support": "SURE"}
    errs = J.validate_ledger_entry(bad)
    assert len(errs) == 4  # claim_id 空 + claim_span 缺 + claim_type 未知 + support 未知
    v = _verdict(ledger=[ok])
    assert J.validate_verdict(v) == []


def test_t13_unsupported_claim_without_runtime_action():
    e = {"claim_id": "c2", "claim_span": "X 早被学界公认", "claim_type": "SCHOLARLY_CONSENSUS",
         "support": "UNSUPPORTED"}
    assert J.validate_ledger_entry(e) == []
    # UNSUPPORTED 只是数据标注: 模块无任何生产导入/动作（T18 静态证明兜底）


# ── T14/T15 — judge 输出 schema 与无 PASS 权限 ────────────────────
def test_t14_judge_output_schema_validation():
    good = J.run_judge({}, transport=_canned(_verdict()))
    assert J.scholarly_mean(good) is not None
    bad = _verdict()
    bad["dimensions"]["textual_grounding"]["score"] = 3.7   # §10: 禁止小数分
    try:
        J.run_judge({}, transport=_canned(bad))
        raise AssertionError("3.7 分应被 schema 拒绝")
    except ValueError:
        pass


def test_t15_judge_cannot_emit_phase_pass():
    v = _verdict()
    v["phase_verdict"] = "O7 PASS"
    try:
        J.run_judge({}, transport=_canned(v))
        raise AssertionError("judge 不得输出阶段 PASS 字段")
    except ValueError:
        pass
    # 常量声明: 测量仪器, 无签发权
    assert J.PRODUCTION_AUTHORITY == 0 and J.EVALUATION_ONLY is True


# ── T16/T17 — seed 与 calibration 案例完备 ────────────────────────
def test_t16_seed_cases_exact_presence():
    seeds = C.seed_cases()
    assert set(seeds) == {"S1", "S2", "S3"}
    assert seeds["S1"]["question"] == "康德"
    assert seeds["S2"]["question"] == "康德为什么认为经验知识不能解释先天综合判断？"
    assert "另一个世界" in seeds["S3"]["question"] and "另一种考察方式" in seeds["S3"]["question"]


def test_t17_calibration_cases_between_5_and_10():
    assert 5 <= len(C.CALIBRATION_CASES) <= 10
    assert len(C.CALIBRATION_CASES) == 8
    traditions = {c["tradition"] for c in C.CALIBRATION_CASES.values()}
    assert {"CHINESE", "EARLY_MODERN", "GERMAN_IDEALISM", "19TH_CENTURY", "20TH_CENTURY"} <= traditions
    # 每例必须定义四要素
    for c in C.CALIBRATION_CASES.values():
        assert c["category"] and c["applicability"] and c["known_pitfalls"] and isinstance(c["bad_flags"], list)


# ── T18 — evaluation 模块零生产导入（AST 静态扫描）────────────────
def test_t18_no_production_imports():
    forbidden = {"engine_langgraph", "final_validator", "quote_bound", "evidence_contract",
                 "agents", "agent_runtime", "tool_contracts", "philo_retrieval", "mcp_client",
                 "config", "routes", "db", "auth"}
    for fname in ("o7_scholarly_judge.py", "o7_scholarly_cases.py"):
        path = os.path.join(EVAL_DIR, fname)
        tree = ast.parse(open(path, encoding="utf-8").read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    root = a.name.split(".")[0]
                    assert root not in forbidden, (fname, a.name)
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".")[0]
                assert root not in forbidden, (fname, node.module)
    # runtime 引擎源也不得反向导入 evaluator
    eng = open(os.path.join(BACKEND, "engine_langgraph.py"), encoding="utf-8").read()
    assert "o7_scholarly_judge" not in eng and "scholarly_claim_ledger" not in eng.lower().replace("scholarly claim ledger", "")


# ── T19 — 生产系统对 BASE 零 diff ────────────────────────────────
def test_t19_no_production_diff_vs_base():
    for rel in ("backend/engine_langgraph.py", "backend/final_validator.py",
                "backend/quote_bound.py", "backend/agents.py", "backend/agent_runtime.py",
                "backend/routes", "backend/evidence_contract.py"):
        r = subprocess.run(["git", "diff", "--quiet", BASE_SHA, "--", rel],
                           cwd=REPO, capture_output=True)
        assert r.returncode == 0, f"{rel} 相对 BASE {BASE_SHA[:9]} 有改动（O7-A 禁止）"


# ── T20 — Q2 交付基线冻结正确（§25）─────────────────────────────
def test_t20_q2_reliability_baseline_frozen():
    b = J.Q2_DELIVERY_BASELINE
    assert b["SAME_SET_SINGLE"] == "22/32 = 68.75%"
    assert b["SAME_SET_MULTI"] == "19/24 = 79.2%"
    assert b["REPAIR_SUCCESS_SINGLE"] == "15/25 = 60%"
    assert b["REPAIR_EXHAUSTION_SINGLE"] == "10/25 = 40%"
    assert b["FRESH_PUBLICATION"] == "13/16 = 81.25%"
    assert b["VALIDATOR_FN"] == 0 and b["VALIDATOR_FP"] == 0 and b["INVALID_FINAL_PUBLIC"] == 0
