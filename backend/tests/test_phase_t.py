# -*- coding: utf-8 -*-
"""Phase T（Tool Architecture Rationalization）契约测试

覆盖任务书 AUTOMATED TESTS 全部条目:
  compare_views      返回结构化 scaffold / 无成品答案权
  dialectic          尊重用户格式约束 / 不强制正反合
  conceptual_map     过程图/概念网络/论证图 + 合法 Mermaid 生成（含 Q13 括号/引号风险回归）
  socratic_tutor     恰好一个问题 / 第二问依赖用户真实回答
  thought_experiment 重入有界
  paper_review/analyze_argument 仲裁（短论证 vs 完整论文）
  citation variants  全部识别/净化
  final runtime phrase 零泄漏
另: taxonomy 覆盖（38 项）/ scaffold 契约 / 重入策略单元 / 所有权审计 / 义务 UNKNOWN。

纯规则测试: LLM 全部 mock, 不联网（search_books 走库内词法/向量检索）。
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

import tool_contracts as TC  # noqa: E402
import semantic_obligations as SO  # noqa: E402
import evidence_contract as EC  # noqa: E402
import final_validator as FV  # noqa: E402
from routes import agent as AG  # noqa: E402
from routes import agent_tools_eval as EV  # noqa: E402
from routes import agent_tools_memory as MEM  # noqa: E402


def _fake_llm(content):
    def _call(messages, **kwargs):
        return {"choices": [{"message": {"content": content}}]}
    return _call


@pytest.fixture(autouse=True)
def _isolated_memory(monkeypatch, tmp_path):
    """隔离运行时记忆文件——防止测试写入污染 backend/data/agent_memory.json
    （真实回归: 测试写入的 default 槽曾使迁移启发式误判, 运行时 thought_experiment KeyError）"""
    import routes.agent_core as AC
    monkeypatch.setattr(AC, "MEM_FILE", tmp_path / "agent_memory_test.json")
    monkeypatch.setattr(AC, "_mem_all", None)
    yield
    monkeypatch.setattr(AC, "_mem_all", None)


def _capture_llm(content):
    """返回 (fake, captured_prompts)——捕获发给内部 LLM 的 prompt"""
    captured = []

    def _call(messages, **kwargs):
        captured.append(messages[-1]["content"] if messages else "")
        return {"choices": [{"message": {"content": content}}]}
    return _call, captured


# ═══════════════════════════════════════════════════════
# T1: Taxonomy 覆盖
# ═══════════════════════════════════════════════════════
class TestTaxonomy:
    def test_full_coverage_38(self):
        philo = {"philosopher_memory", "philosopher_period", "philosopher_style",
                 "philosopher_quote", "philosopher_graph", "philosopher_corpus",
                 "philosopher_concepts", "philosopher_user"}
        assert set(AG.TOOLS) <= set(TC.TOOL_TAXONOMY)
        assert philo <= set(TC.TOOL_TAXONOMY)
        assert len(TC.TOOL_TAXONOMY) == 38

    def test_flags_complete(self):
        flags = {"USES_INTERNAL_LLM", "RETURNS_FINAL_PROSE", "STATEFUL",
                 "EVIDENCE_PRODUCING", "USER_VISIBLE_ARTIFACT", "SAFE_TO_REPEAT"}
        for name, meta in TC.TOOL_TAXONOMY.items():
            assert meta["TOOL_CLASS"] in {"RETRIEVAL", "READ", "STRUCTURED_DATA",
                                          "EXTERNAL_ACTION", "GENERATION", "REASONING_SKILL",
                                          "INTERACTION_MODE", "PRESENTATION", "PERSONA_DATA"}, name
            assert flags <= set(meta), name

    def test_reasoning_skills_not_final_prose(self):
        for name in ("compare_views", "dialectic", "analyze_argument", "paper_review",
                     "thought_experiment", "advisor_council", "conceptual_map"):
            assert TC.TOOL_TAXONOMY[name]["RETURNS_FINAL_PROSE"] is False, name
            assert TC.TOOL_TAXONOMY[name]["USES_INTERNAL_LLM"] is True, name

    def test_artifact_exceptions(self):
        for name in ("write_essay", "essay_outline", "generate_image"):
            assert TC.TOOL_TAXONOMY[name]["USER_VISIBLE_ARTIFACT"] is True, name


# ═══════════════════════════════════════════════════════
# T2: scaffold 契约
# ═══════════════════════════════════════════════════════
class TestScaffoldResult:
    def test_basic(self):
        r = TC.scaffold_result("x_scaffold", "s", confidence=0.7, axes=[1])
        assert r["kind"] == "x_scaffold" and r["reasoning_authority"] == "MAIN_AGENT"
        assert r["axes"] == [1] and r["confidence"] == 0.7

    def test_confidence_clamped(self):
        assert TC.scaffold_result("k", "s", confidence=5)["confidence"] == 1.0


# ═══════════════════════════════════════════════════════
# T3: compare_views → comparison scaffold
# ═══════════════════════════════════════════════════════
SCAFFOLD_JSON = (
    '{"shared_problem": "二者共同面对的问题是欲望如何处置",'
    ' "comparison_axes": [{"axis": "欲望的处置", "side_a": "A 观点", "side_b": "B 观点", "why_it_matters": "决定治疗方向"}],'
    ' "side_a_claims": [{"claim": "主张甲", "basis": "检索材料", "strength": "系统性强"}],'
    ' "side_b_claims": [{"claim": "主张乙", "basis": "reasoning", "strength": "贴合常识"}],'
    ' "strongest_divergence": "欲望本身是否值得保留",'
    ' "evidence_needs": ["核验甲的第3节原文"],'
    ' "candidate_consequences": ["接受甲则快乐被降格"]}'
)


class TestCompareViews:
    def test_returns_structured_scaffold(self, monkeypatch):
        fake, _ = _capture_llm(SCAFFOLD_JSON)
        monkeypatch.setattr(EV, "llm_chat", fake)
        r = EV.TOOLS["compare_views"]["execute"]({"a": "斯多葛主义", "b": "伊壁鸠鲁主义"})
        assert r["kind"] == "comparison_scaffold"
        assert r["reasoning_authority"] == "MAIN_AGENT"
        assert r["comparison_axes"] and r["side_a_claims"] and r["side_b_claims"]
        assert r["strongest_divergence"] and isinstance(r["citations"], list)
        # 不再有成品字段
        assert "comparison" not in r and "image_url" not in r

    def test_no_final_essay_authority_in_description(self):
        desc = AG.TOOLS["compare_views"]["description"]
        assert "结果即成品" not in desc and "直接展示" not in desc
        assert "供主 Agent" in desc and "scaffold" in desc

    def test_internal_llm_prompt_forbids_final_verdict(self, monkeypatch):
        fake, captured = _capture_llm(SCAFFOLD_JSON)
        monkeypatch.setattr(EV, "llm_chat", fake)
        EV.TOOLS["compare_views"]["execute"]({"a": "休谟", "b": "康德"})
        assert any("不得给出最终胜负判断" in p for p in captured)

    def test_fallback_on_bad_llm_output(self, monkeypatch):
        monkeypatch.setattr(EV, "llm_chat", _fake_llm("这不是JSON"))
        r = EV.TOOLS["compare_views"]["execute"]({"a": "休谟", "b": "康德"})
        assert r["kind"] == "comparison_scaffold"
        assert r["evidence_needs"]


# ═══════════════════════════════════════════════════════
# T4: dialectic 去固定正反合 + 约束透传
# ═══════════════════════════════════════════════════════
DIALECTIC_JSON = (
    '{"initial_concept": "自由被理解为任意",'
    ' "internal_tension": "任意即冲动的奴隶",'
    ' "self_negation": "无规则的自由取消自身",'
    ' "new_determination": "自律作为自由的中介",'
    ' "residual_tension": "规则总在异化边缘"}'
)


class TestDialectic:
    def test_dynamic_fields_no_forced_labels(self, monkeypatch):
        fake, _ = _capture_llm(DIALECTIC_JSON)
        monkeypatch.setattr(EV, "llm_chat", fake)
        r = EV.TOOLS["dialectic"]["execute"]({"topic": "自由必须依赖规则"})
        assert r["kind"] == "dialectical_movement"
        assert "internal_tension" in r["movement"]
        text = str(r["movement"])
        for w in ("正题", "反题", "合题", "Thesis", "Antithesis", "Synthesis"):
            assert w not in text and w not in "".join(r["fields_used"])

    def test_honors_user_format_constraint(self, monkeypatch):
        fake, captured = _capture_llm(DIALECTIC_JSON)
        monkeypatch.setattr(EV, "llm_chat", fake)
        r = EV.TOOLS["dialectic"]["execute"](
            {"topic": "宽容是否必须不宽容不宽容者", "constraints": "不要使用正题、反题、合题这些标签"})
        assert any("不要使用正题、反题、合题这些标签" in p for p in captured), "约束必须真正传入工具内部执行层"
        assert r["constraints"] == "不要使用正题、反题、合题这些标签"

    def test_banned_labels_scrubbed(self, monkeypatch):
        bad = ('{"正题": "甲", "internal_tension": "正题：概念自我分裂", "residual_tension": "尚未消解"}')
        monkeypatch.setattr(EV, "llm_chat", _fake_llm(bad))
        r = EV.TOOLS["dialectic"]["execute"]({"topic": "X", "constraints": "禁用标签"})
        assert "正题" not in r["movement"]
        assert "正题" in r["template_labels_removed"] or "正题" not in "".join(r["fields_used"])

    def test_description_declares_no_template(self):
        desc = AG.TOOLS["dialectic"]["description"]
        assert "不使用固定" in desc and "constraints" in desc


# ═══════════════════════════════════════════════════════
# T5: conceptual_map 通用关系图 + 确定性 Mermaid
# ═══════════════════════════════════════════════════════
class TestMermaidRenderer:
    def test_q13_paren_risk_eradicated(self):
        # Q13 风险: 感性(接受性) 圆括号被解析为节点形状; 节点内嵌双引号
        g = {"nodes": [{"id": "感性", "label": "感性(接受性)"},
                       {"id": "知性", "label": '知性——"先验逻辑的"导线'},
                       {"id": "范畴", "label": "范畴(纯知性概念)"}],
             "edges": [{"from": "感性", "to": "知性", "label": "提供杂多"},
                       {"from": "知性", "to": "范畴", "label": ""}]}
        mm = TC.render_mermaid(g, "PROCESS_FLOW")
        v = TC.validate_mermaid(mm, g)
        assert v["ok"], v["errors"]
        assert mm.count('"') % 2 == 0
        # label 全部引号包裹, 无裸括号风险
        for line in mm.splitlines():
            if '["' in line:
                assert line.rstrip().endswith('"]') or '|"' in line

    def test_process_flow_graph(self):
        g = {"nodes": [{"id": "a", "label": "休谟的因果怀疑"}, {"id": "b", "label": "康德的问题重构"},
                       {"id": "c", "label": "范畴"}, {"id": "d", "label": "先验演绎"}],
             "edges": [{"from": "a", "to": "b", "label": "刺激问题"},
                       {"from": "b", "to": "c", "label": "回应"},
                       {"from": "c", "to": "d", "label": "奠基"}]}
        mm = TC.render_mermaid(g, "PROCESS_FLOW")
        v = TC.validate_mermaid(mm, g)
        assert v["ok"] and v["parsed"]["nodes"] == 4 and v["parsed"]["edges"] == 3
        assert mm.startswith("flowchart TD")

    def test_argument_graph_direction(self):
        g = {"nodes": [{"id": "p1", "label": "前提1"}, {"id": "c", "label": "结论"}],
             "edges": [{"from": "p1", "to": "c", "label": "支持"}]}
        mm = TC.render_mermaid(g, "ARGUMENT_GRAPH")
        assert mm.startswith("flowchart TD")
        assert TC.validate_mermaid(mm, g)["ok"]

    def test_concept_network_groups(self):
        g = {"nodes": [{"id": "k", "label": "康德", "group": "德国观念论"},
                       {"id": "h", "label": "黑格尔", "group": "德国观念论"},
                       {"id": "d", "label": "休谟", "group": "英国经验论"}],
             "edges": [{"from": "h", "to": "k", "label": "批判继承"}]}
        mm = TC.render_mermaid(g, "CONCEPT_NETWORK")
        v = TC.validate_mermaid(mm, g)
        assert v["ok"] and "subgraph" in mm

    def test_count_mismatch_detected(self):
        g = {"nodes": [{"id": "a", "label": "A"}], "edges": []}
        mm = TC.render_mermaid(g)
        bad = mm + '\n  n2["幽灵"]'
        v = TC.validate_mermaid(bad, g)
        assert not v["ok"] and any("mismatch" in e for e in v["errors"])


class TestConceptualMap:
    def test_user_specified_process_flow(self, monkeypatch):
        # 用户给链条 → 确定性构图, 不调内部 LLM
        r = EV.TOOLS["conceptual_map"]["execute"]({
            "concept": "康德认识论",
            "map_type": "PROCESS_FLOW",
            "nodes": ["感性", "知性", "范畴", "统觉", "经验对象"],
            "relations": [{"from": "感性", "to": "知性", "label": "提供杂多"},
                          {"from": "知性", "to": "范畴", "label": "综合"},
                          {"from": "范畴", "to": "统觉", "label": "统一于"},
                          {"from": "统觉", "to": "经验对象", "label": "构成"}]})
        assert r["kind"] == "graph_map" and r["map_type"] == "PROCESS_FLOW"
        assert len(r["graph"]["nodes"]) == 5 and len(r["graph"]["edges"]) == 4
        v = TC.validate_mermaid(r["mermaid"], r["graph"])
        assert v["ok"], v["errors"]
        assert r["mermaid_validation"]["ok"]

    def test_llm_graph_json_not_mermaid(self, monkeypatch):
        # 内部 LLM 只产出 graph JSON; 若模型违规直接吐 mermaid 文本 → 不会被采信为结构
        bad = "```mermaid\nflowchart TD\n  a-->b\n```"
        fake, captured = _capture_llm(bad)
        monkeypatch.setattr(EV, "llm_chat", fake)
        r = EV.TOOLS["conceptual_map"]["execute"]({"concept": "虚无主义"})
        assert r["source"] == "retrieval_llm"
        # bad 输出解析不出 graph → 兜底单节点图, 但 mermaid 仍由 renderer 生成且可 parse
        assert TC.validate_mermaid(r["mermaid"], r["graph"])["ok"]

    def test_prompt_requests_graph_json(self, monkeypatch):
        fake, captured = _capture_llm('{"nodes": [{"id": "x", "label": "概念X"}], "edges": []}')
        monkeypatch.setattr(EV, "llm_chat", fake)
        EV.TOOLS["conceptual_map"]["execute"]({"concept": "权力意志"})
        assert any("不要输出 Mermaid" in p for p in captured)

    def test_infer_map_type(self):
        assert TC.infer_map_type("画图展示休谟的因果怀疑→康德的问题重构之间的论证依赖") == "ARGUMENT_GRAPH"
        assert TC.infer_map_type("展示感性→知性→范畴的认识论环节流程") == "PROCESS_FLOW"
        assert TC.infer_map_type("梳理尼采的思想谱系") == "HISTORICAL_GENEALOGY"
        assert TC.infer_map_type("虚无主义的概念关联") == "CONCEPT_NETWORK"


# ═══════════════════════════════════════════════════════
# T6: socratic_tutor stateful one-turn
# ═══════════════════════════════════════════════════════
SOCRATIC_JSON = ('{"diagnosed_assumption": "把真理等同于多数同意",'
                 ' "next_question": "历史上有没有曾经几乎所有人都同意、后来却被证明是错的观念？",'
                 ' "question_purpose": "把同意与为真拆开"}')


class TestSocraticTutor:
    def test_exactly_one_question(self, monkeypatch):
        MEM._mem_slot()["socratic"] = None   # 重置会话状态
        monkeypatch.setattr(EV, "llm_chat", _fake_llm(SOCRATIC_JSON))
        r = EV.TOOLS["socratic_tutor"]["execute"]({"topic": "大家都同意就是真的"})
        assert r["kind"] == "socratic_turn"
        assert r["next_question"].count("？") + r["next_question"].count("?") == 1
        assert "state_update" in r and r["state_update"]["round"] == 1

    def test_schema_one_turn(self):
        props = AG.TOOLS["socratic_tutor"]["parameters"]["properties"]
        assert "rounds" not in props and "user_reply" in props
        assert "ONE CALL = ONE QUESTION" in AG.TOOLS["socratic_tutor"]["description"] or \
               "每次调用只返回一个问题" in AG.TOOLS["socratic_tutor"]["description"]

    def test_multi_question_truncated(self, monkeypatch):
        MEM._mem_slot()["socratic"] = None
        two = '{"next_question": "第一问是这样吗？ 另外你想过那件事吗？", "diagnosed_assumption": "a", "question_purpose": "p"}'
        monkeypatch.setattr(EV, "llm_chat", _fake_llm(two))
        r = EV.TOOLS["socratic_tutor"]["execute"]({"topic": "话题"})
        assert r["next_question"].count("？") == 1

    def test_second_call_depends_on_user_answer(self, monkeypatch):
        MEM._mem_slot()["socratic"] = None
        fake, captured = _capture_llm(SOCRATIC_JSON)
        monkeypatch.setattr(EV, "llm_chat", fake)
        r1 = EV.TOOLS["socratic_tutor"]["execute"]({"topic": "多数同意与真理"})
        reply = "不会，因为事实不会因为投票改变。"
        r2 = EV.TOOLS["socratic_tutor"]["execute"]({"topic": "多数同意与真理", "user_reply": reply})
        # 下一问的生成输入必须包含用户真实回答（不得是预写好的固定第二轮）
        assert any(reply in p for p in captured)
        assert r2["state_update"]["round"] == 2
        assert r1["next_question"] in [q[:len(r1["next_question"])] for q in
                                       (MEM._mem_slot()["socratic"]["asked"] or [])] or \
               MEM._mem_slot()["socratic"]["asked"]

    def test_presentation_hint_hides_inner_fields(self, monkeypatch):
        MEM._mem_slot()["socratic"] = None
        monkeypatch.setattr(EV, "llm_chat", _fake_llm(SOCRATIC_JSON))
        r = EV.TOOLS["socratic_tutor"]["execute"]({"topic": "t"})
        assert "只向用户展示 next_question" in r["presentation_hint"]


# ═══════════════════════════════════════════════════════
# T7: skill reentry
# ═══════════════════════════════════════════════════════
class TestReentry:
    def test_first_call_free(self):
        t = TC.SkillReentryTracker()
        ok, _ = t.admit("thought_experiment", {"base": "全知之镜：AI 预测你的一切选择"})
        assert ok

    def test_degenerate_reentry_rejected(self):
        t = TC.SkillReentryTracker()
        long_base = "全知之镜思想实验：一台超级AI能百分百预测你的一切选择。变体A你不知情照常生活；变体B你知情并当众挑战它"
        t.record("thought_experiment", {"base": long_base}, ok=True)
        ok, why = t.admit("thought_experiment", {"base": "全知之镜"})
        assert not ok and "重入" in why

    def test_user_iteration_allowed(self):
        t = TC.SkillReentryTracker()
        base = "电车难题：五个人绑在轨道上"
        t.record("thought_experiment", {"base": base}, ok=True)
        ok, _ = t.admit("thought_experiment", {"base": f"{base} 改成电车司机亲手扳道岔"},
                        user_message="再来一个变体")
        assert ok

    def test_user_iteration_cap(self):
        t = TC.SkillReentryTracker()
        base = "电车难题：五个人绑在轨道上"
        t.record("thought_experiment", {"base": base}, ok=True)
        t.record("thought_experiment", {"base": base + " 改成司机扳道岔"}, ok=True)
        t.record("thought_experiment", {"base": base + " 改成天桥推人"}, ok=True)
        ok, why = t.admit("thought_experiment", {"base": base + " 改成牺牲一人救五人"},
                          user_message="再来一个变体")
        assert not ok and "上限" in why

    def test_first_result_invalid_allows_retry(self):
        t = TC.SkillReentryTracker()
        base = "缸中之脑"
        t.record("thought_experiment", {"base": base}, ok=False)
        ok, _ = t.admit("thought_experiment", {"base": base})
        assert ok

    def test_new_purpose_allowed(self):
        t = TC.SkillReentryTracker()
        t.record("dialectic", {"topic": "自由与规则"}, ok=True)
        ok, _ = t.admit("dialectic", {"topic": "宽容的悖论"})
        assert ok

    def test_non_skill_tools_unaffected(self):
        t = TC.SkillReentryTracker()
        ok, _ = t.admit("philosopher_debate", {"topic": "x"})
        assert ok

    def test_total_cap(self):
        t = TC.SkillReentryTracker()
        for i in range(4):
            t.record("essay_outline", {"topic": f"完全不同的话题{i}甲乙丙丁"}, ok=True)
        ok, why = t.admit("essay_outline", {"topic": "又一个全新话题丙丁戊己"})
        assert not ok and "上限" in why


# ═══════════════════════════════════════════════════════
# T8: paper_review / analyze_argument 仲裁
# ═══════════════════════════════════════════════════════
class TestArbitration:
    def test_short_argument_routes_to_structure(self, monkeypatch):
        aj = ('{"conclusion": "数学知识来自经验", "premises": [{"premise": "所有知识来自经验", "kind": "explicit"}],'
              ' "hidden_assumptions": ["来源与证成同义"],'
              ' "fallacies": [{"name": "乞题", "where": "P1", "why": "全称前提已含结论"}],'
              ' "weakest_point": "P1 未被论证", "strengthening": ["转攻数学必然性可否被经验修正"]}')
        monkeypatch.setattr(EV, "llm_chat", _fake_llm(aj))
        r = EV.TOOLS["analyze_argument"]["execute"]({"text": "人类所有知识都来自经验。数学知识也是知识。因此数学知识也来自经验。"})
        assert r["kind"] == "argument_structure"
        assert r["argument"]["weakest_point"]
        assert "analysis" not in r   # 旧成品字段不再存在

    def test_full_essay_review_structured(self, monkeypatch):
        rj = ('{"genre_judgment": "完整论文", "thesis": {"statement": "休谟并未摧毁因果性", "clarity": "清晰", "originality": "适中"},'
              ' "structure": {"strengths": ["递进"], "weaknesses": ["反方偏后"]},'
              ' "evidence": {"use": "充分", "gaps": ["缺第二反例"]},'
              ' "strongest_objection": "习惯解释本身预设因果", "writing": "流畅", "contribution": "教科书级",'
              ' "priority_actions": ["前置反方", "补反例"]}')
        monkeypatch.setattr(EV, "llm_chat", _fake_llm(rj))
        r = EV.TOOLS["paper_review"]["execute"]({"text": "一篇完整的论文……" * 20})
        assert r["kind"] == "structured_review"
        assert r["review"]["thesis"]["statement"]

    def test_descriptions_carry_capability_fit(self):
        da = AG.TOOLS["analyze_argument"]["description"]
        dp = AG.TOOLS["paper_review"]["description"]
        assert "单个论证" in da and "paper_review" in da
        assert "完整论文" in dp and "analyze_argument" in dp
        assert "毒舌" not in dp

    def test_system_prompt_arbitration_rule(self):
        import engine_langgraph as EG
        assert "按输入形态与工具能力匹配选择" in EG.SYSTEM_PROMPT_LG


# ═══════════════════════════════════════════════════════
# T9: confrontation textual claim / simulated reply 分离
# ═══════════════════════════════════════════════════════
CONFRONT_JSON = (
    '{"stance_a": {"text": "休谟：因果必然性来自习惯【《人类理解研究》· 第四章】", "basis": "习惯是生命的伟大指南"},'
    ' "stance_b": {"text": "康德：因果范畴是经验可能性的条件【《纯粹理性批判》· 先验演绎】", "basis": "知性为自然立法"},'
    ' "exchanges": ["模拟：休谟反问统觉统一是否另一种习惯性虚构", "模拟：康德反打习惯解释是循环"],'
    ' "referee_note": "候选: 双方最强/最弱与合题方向"}'
)


class TestConfrontation:
    def test_structured_card_with_separation(self, monkeypatch):
        monkeypatch.setattr(EV, "llm_chat", _fake_llm(CONFRONT_JSON))
        r = EV.TOOLS["confrontation"]["execute"]({"topic": "因果必然性到底来自哪里", "a": "休谟", "b": "康德"})
        assert r["kind"] == "confrontation_card"
        assert r["stance_a"]["text"] and r["stance_b"]["text"]
        assert r["exchanges"] and r["referee_note"]
        assert r["citations"] and isinstance(r["evidence"], list)
        assert "均来自库内原文片段" not in str(r.get("summary"))   # 不再单方面声称已核验
        ph = r["presentation_hint"]
        assert "textual claim" in ph and "模拟" in ph and "主 Agent" in ph


# ═══════════════════════════════════════════════════════
# T13-A: citation variants
# ═══════════════════════════════════════════════════════
class TestCitationVariants:
    def test_canonical(self):
        assert EC._cite_markers("见【《理想国》·第十卷】此处") == [("理想国", "第十卷")]

    def test_book_only(self):
        assert EC._cite_markers("【《瓦格纳事件》】") == [("瓦格纳事件", "")]

    def test_book_chapter_merged(self):
        assert EC._cite_markers("【《康德著作集·序言》】") == [("康德著作集", "序言")]

    def test_book_plus_number(self):
        assert EC._cite_markers("【《50堂经典哲学思维课》47】") == [("50堂经典哲学思维课", "47")]

    def test_author_work_variant(self):
        assert EC._cite_markers("【维拉莫维茨·《未来语文学！》】") == [("未来语文学！", "")]

    def test_all_variants_in_one_text(self):
        text = ("甲【《理想国》·第十卷】乙【《康德著作集·序言》】丙【《快乐的科学》125】"
                "丁【《瓦格纳事件》】戊【维拉莫维茨·《未来语文学！》】")
        markers = EC._cite_markers(text)
        assert len(markers) == 5

    def test_citation_validation_verifies_author_work(self):
        # O2 改写: LiveCitationSanitizer 已删——check_citations 只检测不改写
        log = [{"name": "search_books", "args": {"query": "x"},
                "result_full": {"results": [{"book_title": "未来语文学！", "chapter_title": "",
                                             "author": "维拉莫维茨", "snippet": "反语文学的檄文"}]}}]
        ans = "他说这是【维拉莫维茨·《未来语文学！》】中的立场。"
        verified, issues = FV.check_citations(ans, log)
        assert verified == 1 and issues == []
        assert "【维拉莫维茨·《未来语文学！》】" in ans, "verified 引用原样保留在文本中"

    def test_citation_validation_reports_author_work_not_downgrade(self):
        # 旧契约（未核验 author-work 引用降级为一般提及）已废除——
        # 返回 UNVERIFIED_CITATION issue, 正文零改动
        ans = "他说这是【维拉莫维茨·《未来语文学！》】中的立场。"
        verified, issues = FV.check_citations(ans, [])
        assert verified == 0
        assert [i.code for i in issues] == [FV.UNVERIFIED_CITATION]
        assert issues[0].locator == "【维拉莫维茨·《未来语文学！》】"
        assert "【维拉莫维茨·《未来语文学！》】" in ans and "维拉莫维茨" in ans, "文本不被改写"

    def test_sanitize_citations_covers_variants(self):
        tool_log = [{"name": "search_books", "args": {"query": "x"},
                     "result_full": {"results": [{"book_title": "理想国", "chapter_title": "第十卷",
                                                  "author": "柏拉图", "snippet": "拒绝模仿"}]}}]
        ans = "依据【《理想国》·第十卷】与【维拉莫维茨·《未来语文学！》】。"
        rep = EC.sanitize_citations(ans, tool_log=tool_log)
        kinds = {a["book"] for a in rep["actions"] if a["action"] == "verified"}
        assert "理想国" in kinds
        assert any(a["action"] == "downgraded_plain_mention" and a["book"] == "未来语文学！"
                   for a in rep["actions"])

    def test_unverified_citations_variant(self):
        out = EC._unverified_citations("引用了【《不存在的书·某章》】和【某人·《不存在作品》】", [])
        assert len(out) == 2


# ═══════════════════════════════════════════════════════
# T13-B: runtime phrase 不进 Final
# ═══════════════════════════════════════════════════════
class TestRuntimePhrases:
    def test_strip_all_phrases(self):
        text = "检索已被收口，我基于现有材料完成回答。工具预算已达上限，因此这里作答。"
        out = TC.strip_runtime_phrases(text)
        for ph in TC.RUNTIME_PHRASES:
            assert ph not in out
        assert "我基于现有材料完成回答" in out

    def test_stream_scrubber_no_leak_across_chunks(self):
        s = TC.RuntimePhraseScrubber()
        out = s.push("这一步的判断是：")
        out += s.push("检")
        out += s.push("索已被收口，基于材料作答。")
        out += s.flush()
        assert "检索已被收口" not in out
        assert "基于材料作答" in out

    def test_clean_text_untouched(self):
        text = "康德认为范畴是经验可能性的条件。"
        assert TC.strip_runtime_phrases(text) == text


# ═══════════════════════════════════════════════════════
# T13-C: 高层义务 UNKNOWN
# ═══════════════════════════════════════════════════════
class TestObligationUnknown:
    OB = [{"type": "alternative_interpretation", "status": "REQUIRED", "source": "t"},
          {"type": "uncertainty_disclosure", "status": "REQUIRED", "source": "t"},
          {"type": "counterfactual_boundary", "status": "REQUIRED", "source": "t"}]

    def test_high_level_miss_is_unknown(self):
        res = SO.assess_obligations(self.OB, "这是一个不含任何限定语的直接断言回答。")
        by_type = {o["type"]: o["status"] for o in res}
        assert by_type["alternative_interpretation"] == "UNKNOWN"
        assert by_type["uncertainty_disclosure"] == "UNKNOWN"

    def test_hit_still_satisfied(self):
        res = SO.assess_obligations(self.OB, "另一种读法是把它理解为自我规定，且这并非唯一的解释。")
        by_type = {o["type"]: o["status"] for o in res}
        assert by_type["alternative_interpretation"] == "SATISFIED"

    def test_factual_obligation_remains_two_state(self):
        res = SO.assess_obligations(self.OB, "直接断言。")
        by_type = {o["type"]: o["status"] for o in res}
        assert by_type["counterfactual_boundary"] in ("UNSATISFIED", "SATISFIED")
        assert by_type["counterfactual_boundary"] != "UNKNOWN"

    def test_unknown_never_appends(self):
        assert SO.unsatisfied(self.OB, "断言回答。") == [] or all(
            o["status"] == "UNSATISFIED" for o in SO.unsatisfied(self.OB, "断言回答。"))


# ═══════════════════════════════════════════════════════
# T12: ownership audit
# ═══════════════════════════════════════════════════════
class TestOwnershipAudit:
    def test_bypassed_specialized_detected(self):
        tool_log = [
            {"name": "search_books", "args": {"query": "x"}, "thought": "执行 search_books",
             "result_full": {"results": [{"book_title": "理想国", "chapter_title": "第十卷",
                                          "snippet": "拒绝模仿的诗人应当被逐出城邦"}]}},
            {"name": "conceptual_map", "args": {"concept": "康德认识论"}, "thought": "执行 conceptual_map",
             "result_full": {"kind": "graph_map", "summary": "一张与答案毫无关系的图",
                             "graph": {"nodes": [{"id": "a", "label": "某个完全没被使用的节点标签甲乙丙丁"}], "edges": []}}},
        ]
        ans = "最终回答完全自写, 与图无关。"
        audit = TC.tool_ownership_audit(tool_log, ans)
        entry = [e for e in audit["entries"] if e["tool"] == "conceptual_map"][0]
        assert entry["final_use"] == "BYPASSED"
        assert audit["bypassed_specialized_tools"] == 1

    def test_used_scaffold(self):
        frag = "比较轴线之一是欲望的处置方式这条轴线非常关键"
        tool_log = [{"name": "compare_views", "args": {"a": "a", "b": "b"}, "thought": "执行 compare_views",
                     "result_full": {"kind": "comparison_scaffold",
                                     "comparison_axes": [{"axis": frag}]}}]
        ans = f"回答中引用了 {frag} 作为骨架。"
        audit = TC.tool_ownership_audit(tool_log, ans)
        entry = [e for e in audit["entries"] if e["tool"] == "compare_views"][0]
        assert entry["final_use"] in ("USED", "PARTIALLY_USED")
        assert audit["bypassed_specialized_tools"] == 0

    def test_not_admitted_specialized_redundant(self):
        tool_log = [{"name": "thought_experiment", "args": {"base": "x"},
                     "thought": "检索准入未通过，执行前取消",
                     "result_full": {"error": "重入拦截"}}]
        audit = TC.tool_ownership_audit(tool_log, "回答")
        entry = audit["entries"][0]
        assert entry["tool_value"] == "REDUNDANT"
        assert audit["redundant_specialized_tools"] == 1

    def test_retrieval_not_counted_as_specialized(self):
        tool_log = [{"name": "search_books", "args": {"query": "x"}, "thought": "执行 search_books",
                     "result_full": {"results": []}}]
        audit = TC.tool_ownership_audit(tool_log, "回答")
        assert audit["redundant_specialized_tools"] == 0
        assert audit["entries"][0]["tool_value"] == "NEW_EVIDENCE"


# ═══════════════════════════════════════════════════════
# T7: thought_experiment 工具契约（结构化 + 描述声明重入约束）
# ═══════════════════════════════════════════════════════
class TestThoughtExperiment:
    def test_structured_scaffold(self, monkeypatch):
        MEM._mem_slot()["experiment"] = None
        tj = ('{"setting": "全知之镜：AI 在你决定前数秒准确预测你的选择",'
              ' "stance_projections": [{"stance": "相容论", "projection": "预测不排除自由"},'
              ' {"stance": "自由意志论", "projection": "别样可能性被取消"},'
              ' {"stance": " hard determinism", "projection": "自由的直觉是幻觉"}],'
              ' "revealed_problem": "自由是否需要开放可能性"}')
        monkeypatch.setattr(MEM, "llm_chat", _fake_llm(tj))
        r = MEM.TOOLS["thought_experiment"]["execute"]({"base": "全知之镜"})
        assert r["kind"] == "thought_experiment_scaffold"
        assert r["setting"] and len(r["stance_projections"]) == 3
        assert "experiment" not in r   # 旧成品字段不再存在

    def test_description_declares_reentry(self):
        assert "重入策略" in AG.TOOLS["thought_experiment"]["description"]

    def test_memory_slot_updated(self, monkeypatch):
        MEM._mem_slot()["experiment"] = None
        monkeypatch.setattr(MEM, "llm_chat", _fake_llm(
            '{"setting": "S", "stance_projections": [], "revealed_problem": "P"}'))
        MEM.TOOLS["thought_experiment"]["execute"]({"base": "体验机"})
        assert MEM._mem_slot()["experiment"]["base"] == "体验机"


# ═══════════════════════════════════════════════════════
# T11: 路由原则进入系统提示
# ═══════════════════════════════════════════════════════
class TestRouterPrinciple:
    def test_capability_fit_rule_present(self):
        import engine_langgraph as EG
        p = EG.SYSTEM_PROMPT_LG
        assert "能力匹配 × 信息增益 × 输出合同匹配" in p
        assert "允许不调用" in p
        assert "有效" in p and "专用工具" in p

    def test_scaffold_ownership_rule_present(self):
        import engine_langgraph as EG
        p = EG.SYSTEM_PROMPT_LG
        assert "结构化脚手架" in p and "二次综合" in p
        assert "USER_REQUESTED_ARTIFACT" in p

    def test_runtime_phrase_rule_present(self):
        import engine_langgraph as EG
        assert "内部过程措辞" in EG.SYSTEM_PROMPT_LG
