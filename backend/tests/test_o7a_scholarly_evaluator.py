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
    assert gate["false_fatal_assertions"] == []       # 无预期 flag 的 fixture 零误报


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
    # O7-B §14（2026-09-06 Reviewer 授权）: get_book_detail/get_chapter 允许 additive
    # 书目元数据暴露 → backend/routes 的冻结基线改对照 O7-B BASE；认知/校验/引文
    # 核心文件仍硬冻结于 O7-A BASE，O7-B §24 四项 PRODUCTION_POLICY DIFF=0 不变。
    O7B_BASE = "68ed56d07"  # O7-C §59 授权的工具注册/执行器改动落地 commit
    hard = ("backend/engine_langgraph.py", "backend/final_validator.py",
            "backend/quote_bound.py", "backend/agents.py", "backend/agent_runtime.py",
            "backend/evidence_contract.py")
    for rel in hard:
        r = subprocess.run(["git", "diff", "--quiet", BASE_SHA, "--", rel],
                           cwd=REPO, capture_output=True)
        assert r.returncode == 0, f"{rel} 相对 BASE {BASE_SHA[:9]} 有改动（O7-A 禁止）"
    r = subprocess.run(["git", "diff", "--quiet", O7B_BASE, "--", "backend/routes"],
                       cwd=REPO, capture_output=True)
    assert r.returncode == 0, "backend/routes 相对 O7-B BASE 有未授权改动"


# ── T20 — Q2 交付基线冻结正确（§25）─────────────────────────────
def test_t20_q2_reliability_baseline_frozen():
    b = J.Q2_DELIVERY_BASELINE
    assert b["SAME_SET_SINGLE"] == "22/32 = 68.75%"
    assert b["SAME_SET_MULTI"] == "19/24 = 79.2%"
    assert b["REPAIR_SUCCESS_SINGLE"] == "15/25 = 60%"
    assert b["REPAIR_EXHAUSTION_SINGLE"] == "10/25 = 40%"
    assert b["FRESH_PUBLICATION"] == "13/16 = 81.25%"
    assert b["VALIDATOR_FN"] == 0 and b["VALIDATOR_FP"] == 0 and b["INVALID_FINAL_PUBLIC"] == 0


# ═══════════════════════════════════════════════════════
# O7-A RP1（Judge Calibration Closure）R1–R15
# ═══════════════════════════════════════════════════════
import hashlib

_ORIG_C6_L1_ANSWER = ("根据记录，该文第二节提出了语用转向论证，第三节给出对定义主义的三个反驳——"
                      "作者的结论是语言游戏不可定义。")


def test_r1_original_c6_l1_bad_unchanged():
    fx = C.ACCESS_FIXTURES["C6-L1-bad"]
    ans = fx["judge_input"]["ANSWER"]
    assert ans == _ORIG_C6_L1_ANSWER, "kill case 文本被改动（必须原样冻结）"
    assert hashlib.sha256(ans.encode("utf-8")).hexdigest() == (
        "65cd5c06f83f25d7a37de378a28731c24ffbc00141f850acc74b923409d5ea0b")
    assert fx["expect_flags"] == ["LITERATURE_ACCESS_OVERCLAIM"]
    rec = fx["judge_input"]["SECONDARY_SOURCE_RECORDS"][0]
    assert rec["access_level"] == "METADATA_ONLY"


def test_r2_metadata_only_internal_section_overclaim_is_f6():
    # F6-M1: METADATA_ONLY + 章节级主张 → 唯一正确的 flag 是 F6（一般规则可覆盖）
    assert C.ACCESS_FIXTURES["F6-M1-bad"]["expect_flags"] == ["LITERATURE_ACCESS_OVERCLAIM"]


def test_r3_hedge_does_not_elevate_access():
    # F6-M2: "根据数据库记录，作者最终证明……"（带 hedge）仍然 F6 —— 一般规则明示
    # 修辞性来源声明不提高访问级别; 该规则必须以一般形式存在
    assert C.ACCESS_FIXTURES["F6-M2-bad"]["expect_flags"] == ["LITERATURE_ACCESS_OVERCLAIM"]
    assert "不提高实际访问级别" in J.JUDGE_SYSTEM_PROMPT


def test_r4_metadata_existence_claim_alone_no_f6():
    # C6-good/mid 只转述书目条目 → 设计上无致命错误（negative pool）
    for fid in ("C6-good", "C6-mid"):
        assert C.calibration_fixtures()[fid]["expect_flags"] == []


def test_r5_abstract_supported_claim_no_f6():
    assert C.ACCESS_FIXTURES["F6-M3-good"]["expect_flags"] == []
    assert C.ACCESS_FIXTURES["C6-L2-good"]["expect_flags"] == []


def test_r6_abstract_beyond_supplied_content_is_f6():
    # L1（摘要外章节内容）与 M4（FULL_TEXT_AVAILABLE≠READ）都是越界
    assert C.ACCESS_FIXTURES["C6-L1-bad"]["expect_flags"] == ["LITERATURE_ACCESS_OVERCLAIM"]
    assert C.ACCESS_FIXTURES["F6-M4-bad"]["expect_flags"] == ["LITERATURE_ACCESS_OVERCLAIM"]


def test_r7_full_text_available_is_not_full_text_read():
    rec = C.ACCESS_FIXTURES["F6-M4-bad"]["judge_input"]["SECONDARY_SOURCE_RECORDS"][0]
    assert rec["access_level"] == "FULL_TEXT_AVAILABLE"
    assert "FULL_TEXT_AVAILABLE" in J.ACCESS_LEVELS and "FULL_TEXT_READ" in J.ACCESS_LEVELS
    # judge 宪法必须包含"可获取≠已读"的一般规则
    assert "不等于已读" in J.JUDGE_SYSTEM_PROMPT


def test_r8_full_text_read_supported_claim_no_f6():
    assert C.ACCESS_FIXTURES["F6-M5-good"]["expect_flags"] == []
    assert C.ACCESS_FIXTURES["C6-L3-good"]["expect_flags"] == []


def test_r9_fatal_recall_denominator_uses_flag_assertions():
    # C6-bad 植入 F1+F6 两个断言 → 分母按 flag 计数=+2, 不是按 fixture 计数=+1
    results = {"C6-bad": _verdict(flags={"FABRICATED_BIBLIOGRAPHY"})}
    gate = J.calibration_gate(results, {"C6-bad": ["FABRICATED_BIBLIOGRAPHY",
                                                   "LITERATURE_ACCESS_OVERCLAIM"]})
    assert gate["expected_fatal_total"] == 2
    assert gate["expected_fatal_detected"] == 1
    assert gate["expected_fatal_recall"] == 0.5
    assert gate["per_flag_recall"]["FABRICATED_BIBLIOGRAPHY"] == 1.0
    assert gate["per_flag_recall"]["LITERATURE_ACCESS_OVERCLAIM"] == 0.0


def test_r10_per_dimension_applicability_agreement_calculation():
    va = _verdict(applic={"literature_orientation": "OPTIONAL"})
    vb = _verdict(applic={"literature_orientation": "REQUIRED"})   # 1/5 不同
    m = J.applicability_metrics({"x": va}, {"x": vb})
    assert m["per_dimension_applicability_exact_agreement"] == 0.8
    assert m["required_na_critical_contradictions"] == 0
    assert m["whole_vector_exact_agreement"] == 0.0


def test_r11_whole_vector_metric_is_diagnostic_only():
    # 门指标 = per-dimension; 整向量仅诊断记录（键名与角色固定）
    va = _verdict(applic={"interpretive_plurality": "NOT_APPLICABLE"})
    vb = _verdict(applic={"interpretive_plurality": "NOT_APPLICABLE"})
    m = J.applicability_metrics({"x": va}, {"x": vb})
    assert m["whole_vector_exact_agreement"] == 1.0   # 诊断值可以=1, 但不作为硬门键
    assert "per_dimension_applicability_exact_agreement" in m
    assert J.PRODUCTION_AUTHORITY == 0                # 聚合层无任何生产权限语义


def test_r12_required_na_critical_contradiction_counted():
    va = _verdict(applic={"historical_discipline": "REQUIRED"})
    vb = _verdict(applic={"historical_discipline": "NOT_APPLICABLE"})
    m = J.applicability_metrics({"x": va}, {"x": vb})
    assert m["required_na_critical_contradictions"] == 1
    assert m["per_dimension_applicability_exact_agreement"] == 0.8


def test_r13_optional_instability_still_visible():
    va = _verdict(applic={"textual_grounding": "OPTIONAL"})
    vb = _verdict(applic={"textual_grounding": "REQUIRED"})   # OPTIONAL↔REQUIRED: 非临界, 但降一致率
    m = J.applicability_metrics({"x": va}, {"x": vb})
    assert m["per_dimension_applicability_exact_agreement"] == 0.8
    assert m["required_na_critical_contradictions"] == 0


def test_r14_no_fixture_specific_judge_rule():
    prompt = J.JUDGE_SYSTEM_PROMPT
    for banned in ("C6", "L1", "M1", "第二节", "语用转向", "图型", "朝三暮四",
                   "Wittgenstein", "Becker", "Ivanov", "Park", "语言游戏"):
        assert banned not in prompt, f"judge 宪法含 fixture 专属规则: {banned}"


def test_r15_no_production_imports_and_diff():
    # 复用 T18/T19 逻辑（RP1 后重申）
    test_t18_no_production_imports()
    test_t19_no_production_diff_vs_base()


# ═══════════════════════════════════════════════════════
# O7-A RP2 — Hybrid Judge（QuoteSupportProbe + k-of-3 ensemble）T1–T21
# ═══════════════════════════════════════════════════════
import o7_quote_probe as QP

_E = ["先进篇正文……子曰：“夫人不言，言必有中。”"]


def test_t1_quote_probe_exact():
    r = QP.probe("原文：“夫人不言，言必有中。”", _E, "COMPLETE_FOR_FIXTURE")
    assert r["spans"] and r["spans"][0]["support_status"] == "EXACT"
    assert r["mechanical_f5"] is False


def test_t2_quote_probe_near():
    ev = "先进篇正文……子曰：“夫人不言，言必有中。”"
    r = QP.probe("原文：“夫人不言，言必有中呀。”", [ev], "COMPLETE_FOR_FIXTURE")
    assert r["spans"][0]["support_status"] == "NEAR"
    assert r["mechanical_f5"] is True


def test_t3_quote_probe_none():
    r = QP.probe("康德逐字写道：“图型是隐藏在人类灵魂深处的技艺。”",
                 ["《纯粹理性批判》译文：图型法与想象力……"], "COMPLETE_FOR_FIXTURE")
    assert r["spans"][0]["support_status"] == "NONE"
    assert r["mechanical_f5"] is True


def test_t4_normal_paraphrase_not_exact_quote():
    r = QP.probe("康德的意思大致是：图型的运用是一种深层技术（转述）。", [_E[0]], "COMPLETE_FOR_FIXTURE")
    assert r["spans"] == [] and r["mechanical_f5"] is False


def test_t5_book_title_not_quote():
    r = QP.probe("这一思想记录在《纯粹理性批判》中。", [_E[0]], "COMPLETE_FOR_FIXTURE")
    assert r["spans"] == [] and r["mechanical_f5"] is False


def test_t6_blockquote_unsupported():
    r = QP.probe("我的解读：\n\n> 所谓图型，就是我此刻想到的连接机制。\n", [], "COMPLETE_FOR_FIXTURE")
    assert r["spans"] and r["spans"][0]["kind"] == "blockquote"
    assert r["spans"][0]["support_status"] == "NONE" and r["mechanical_f5"] is True


def test_t7_partial_evidence_not_globally_false():
    r = QP.probe("尼采逐字写道：“权力意志是一种手段而非目的。”",
                 ["《查拉图斯特拉如是说》选段（与本句无关）"], "PARTIAL_RUNTIME_EVIDENCE")
    assert r["mechanical_f5"] is None          # PARTIAL 不可机械定 F5
    assert r["spans"][0]["support_status"] == "NONE"


def _mk(score=3, appl="REQUIRED", flags=None):
    return _verdict(scores={d: score for d in J.DIMENSIONS},
                    applic={d: appl for d in J.DIMENSIONS}, flags=flags)


def test_t8_mechanical_f5_authority_on_complete():
    llm = [_mk(flags=set()), _mk(flags=set()), _mk(flags=set())]   # LLM 全说无 F5
    agg = J.aggregate_ensemble(llm, mechanical_f5=True, evidence_scope="COMPLETE_FOR_FIXTURE")
    assert agg["fatal_flags"]["FALSE_EXACT_QUOTE"]["value"] is True   # 机械权威覆盖
    assert agg["mechanical_llm_conflict"] and agg["review_required"] is True


def test_t9_mechanical_f5_non_authority_on_partial():
    llm = [_mk(flags={"FALSE_EXACT_QUOTE"}), _mk(flags=set()), _mk(flags=set())]
    agg = J.aggregate_ensemble(llm, mechanical_f5=None, evidence_scope="PARTIAL_RUNTIME_EVIDENCE")
    assert agg["fatal_flags"]["FALSE_EXACT_QUOTE"]["value"] is False   # 多数决定, 机械不介入


def test_t10_median_score_aggregation():
    v3 = [_verdict(scores={d: s for d in J.DIMENSIONS}) for s in (2, 3, 4)]
    agg = J.aggregate_ensemble(v3)
    assert all(dd["score"] == 3 for dd in agg["dimensions"].values())


def test_t11_majority_applicability_aggregation():
    vs = [_verdict(), _verdict(), _verdict(applic={"literature_orientation": "OPTIONAL"})]
    agg = J.aggregate_ensemble(vs)
    assert agg["dimensions"]["literature_orientation"]["applicability"] == "REQUIRED"


def test_t12_one_one_one_applicability_ambiguous():
    apps = ["REQUIRED", "OPTIONAL", "NOT_APPLICABLE"]
    vs = [_verdict(applic={d: apps[i] for d in J.DIMENSIONS}) for i in range(3)]
    agg = J.aggregate_ensemble(vs)
    assert all(dd["applicability"] == "AMBIGUOUS" for dd in agg["dimensions"].values())
    assert agg["review_required"] is True


def test_t13_majority_semantic_fatal_aggregation():
    vs = [_mk(flags={"FABRICATED_BIBLIOGRAPHY"}), _mk(), _mk()]
    agg = J.aggregate_ensemble(vs)
    assert agg["fatal_flags"]["FABRICATED_BIBLIOGRAPHY"]["value"] is False   # 1/3 → false
    vs2 = [_mk(flags={"FABRICATED_BIBLIOGRAPHY"}), _mk(flags={"FABRICATED_BIBLIOGRAPHY"}), _mk()]
    assert J.aggregate_ensemble(vs2)["fatal_flags"]["FABRICATED_BIBLIOGRAPHY"]["value"] is True


def test_t14_raw_judgments_preserved():
    vs = [_mk(), _mk(), _mk()]
    agg = J.aggregate_ensemble(vs, mechanical_f5=False)
    assert len(agg["raw_judgments"]) == 3 and agg["raw_judgments"] == vs


def test_t15_minority_dissent_preserved():
    vs = [_mk(flags={"FABRICATED_BIBLIOGRAPHY"}), _mk(), _mk()]
    agg = J.aggregate_ensemble(vs)
    assert agg["minority_flags"] == [{"flag": "FABRICATED_BIBLIOGRAPHY", "votes": [True, False, False]}]


def test_t16_two_ensemble_comparison():
    aggA = J.aggregate_ensemble([_mk(), _mk(), _mk()])
    aggB = J.aggregate_ensemble([_mk(), _mk(score=4), _mk(score=4)])
    stab = J.stability_compare({"x": aggA}, {"x": aggB})
    assert "per_dimension_applicability_exact_agreement" in stab


def test_t17_fatal_assertion_denominator():
    assert C.expected_fatal_flags()  # 语义 flag 断言集非空
    assert sum(len(v) for v in C.expected_fatal_flags().values()) >= 12


def test_t18_false_fatal_negative_pool():
    neg = ["g1"]
    gate = J.calibration_gate({"g1": _mk(flags={"MAJOR_ANACHRONISM"})}, {},
                              negative_pool=neg)
    assert gate["false_fatal_assertions"] == [("g1", "MAJOR_ANACHRONISM")]


def test_t19_reviewer_manifest_conflict():
    llm = [_mk(), _mk(), _mk()]
    agg = J.aggregate_ensemble(llm, mechanical_f5=True, evidence_scope="COMPLETE_FOR_FIXTURE")
    mf = J.ensemble_manifest({"C2-bad": agg})
    assert mf["MECHANICAL_LLM_CONFLICT"] == ["C2-bad"]
    assert mf["ANY_1_OF_3_FATAL_DISSENT"] == []


def test_t20_no_semantic_prompt_tuning():
    # 语义 judge 宪法相对 RP1 冻结（RP2 只新增机械组件; 措辞含 RP1 已授权的一般规则）
    assert "访问级别上限" in J.JUDGE_SYSTEM_PROMPT
    for banned in ("C2", "C6", "L1", "Q5", "直觉是对象直接呈现", "朝三暮四"):
        assert banned not in J.JUDGE_SYSTEM_PROMPT


def test_t21_no_production_imports_and_diff():
    test_t18_no_production_imports()
    test_t19_no_production_diff_vs_base()
