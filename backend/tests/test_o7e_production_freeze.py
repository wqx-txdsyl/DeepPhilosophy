# -*- coding: utf-8 -*-
"""O7-E Production Freeze: P 套件——Local Patch 生产启用合同。

锁死（Reviewer 2026-09-09 签署 PRODUCTION_FREEZE_AUTHORIZED=true 后的任务书 §A/§B）:
  P1 General Agent 生产默认走 production adapter（LOCAL_PATCH 真实启用）
  P2 哲学家 Agent 零改——无 adapter, 永走 FULL_REWRITE（PHILOSOPHER_AGENT_DIFF=0）
  P3 LOCAL_PATCH_ADAPTER_OWNER=1——评测 runner 与生产共用同一 adapter 类
  P4 LOCAL_PATCH_PRODUCTION_ENABLED 生产默认 true
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine_langgraph as EG
import routes.agent as AG

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_o2_final_ownership import (_msg, _done, _answer_text, _TOOLS_SCRIPT,
                                     _SENTINEL_FAKE, ScriptedChat, _fake_tools,
                                     _STUB_CALLS)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools", "evaluation"))
import local_patch_runtime as LPR
import o7e_rca1_hook_eval as EVAL


def _run_prod(question, script, agent="general"):
    """无 seam 注入——真实 production 默认路径。"""
    for k in _STUB_CALLS:
        _STUB_CALLS[k] = []
    orig = (EG.get_llm, EG.get_tools, AG.llm_chat)
    chat = ScriptedChat(script=list(script))
    EG.get_llm = lambda: chat
    EG.get_tools = lambda agent_: _fake_tools()
    AG.llm_chat = lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("收口路径不得调用隐藏 LLM"))

    async def _collect():
        evs = []
        async for ev in EG.stream_agent(question, [], agent=agent, language="zh"):
            evs.append(ev)
        return evs
    try:
        return asyncio.run(_collect())
    finally:
        EG.get_llm, EG.get_tools, AG.llm_chat = orig


_GOOD = "经重新整理：逐字核验后确认，「言必有中」出自孔子对闵子骞的评价。"
_PARA = "孔子在此批评鲁人改建长府，并借闵子骞之言说明行事应遵循成规，言语贵在切中要害。"
_PATCH = None   # 延迟构造（依赖 RC 的 slice catalog 不必要——PARAPHRASE 无需 catalog）


def test_p1_general_agent_uses_production_adapter():
    import json
    bad = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    patch = json.dumps({"patches": [
        {"issue_id": "vi_1", "action": "PARAPHRASE_CLAIM",
         "replacement_text": _PARA}]}, ensure_ascii=False)
    script = _TOOLS_SCRIPT + [_msg(bad), _msg(patch)]
    evs = _run_prod("言必有中出处", script, agent="general")
    done = _done(evs)
    trace = done["validation"]["repair_trace"]
    assert len(trace) == 1
    assert trace[0]["repair_output_mode"] == "LOCAL_PATCH"
    assert trace[0]["adapter_owner"] == "production"   # 无 seam 注入 → 生产 adapter
    assert trace[0]["lp_gate"]["supported"] is True
    assert done["validation"]["repairs_used"] == 1
    assert done["validation"]["result"]["ok"] is True
    assert "切中要害" in _answer_text(evs)


def test_p2_philosopher_agent_stays_full_rewrite():
    bad = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    script = _TOOLS_SCRIPT + [_msg(bad), _msg(_GOOD)]
    evs = _run_prod("言必有中出处", script, agent="nietzsche")
    done = _done(evs)
    trace = done["validation"]["repair_trace"]
    assert len(trace) == 1
    assert trace[0]["repair_output_mode"] == "FULL_REWRITE"   # 哲学家永不 LOCAL_PATCH
    assert trace[0]["adapter_owner"] == "none"
    assert done["validation"]["result"]["ok"] is True


def test_p3_adapter_owner_single_source():
    # LOCAL_PATCH_ADAPTER_OWNER=1: 评测 runner 与生产共用同一个 adapter 类
    assert EVAL.LocalPatchAdapter is LPR.LocalPatchAdapter
    assert isinstance(LPR.production_adapter(), LPR.LocalPatchAdapter)
    assert LPR.production_adapter() is LPR.production_adapter()   # 单例


def test_p4_production_enabled_by_default():
    assert EG.LOCAL_PATCH_PRODUCTION_ENABLED is True
    assert EG._LOCAL_PATCH_PRODUCTION_AGENTS == {"general"}


# ═══════════════════════════════════════════════════════
# PF-RP1 §A: action 合同单一真源——三方 drift 锁死
# ═══════════════════════════════════════════════════════
def test_p5_action_matrix_system_human_applier_equal():
    import json
    import re as _re
    import repair_context as RC
    matrix = RC.LOCAL_PATCH_ACTION_MATRIX
    assert matrix == {"quote": ("COPY_SLICE", "PARAPHRASE_CLAIM"),
                      "citation": ("COPY_SLICE", "REPLACE_TEXT")}
    # ① System protocol 文本逐 kind 列出矩阵动作, 且不得再宣称 quote 可 REPLACE_TEXT
    eng = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)), ), "engine_langgraph.py"), encoding="utf-8").read()
    proto = eng.split('LOCAL_PATCH_SYSTEM_PROTOCOL = """')[1].split('"""')[0]
    block = proto[proto.index("- kind=quote"):proto.index("quote 上使用")]
    q_seg = block[:block.index("- kind=citation")]
    c_seg = block[block.index("- kind=citation"):]
    for act in matrix["quote"]:
        assert act in q_seg, f"System protocol quote 段缺 {act}"
    for act in matrix["citation"]:
        assert act in c_seg, f"System protocol citation 段缺 {act}"
    assert "REPLACE_TEXT" not in q_seg            # 旧漂移文本已清除
    assert "PARAPHRASE_CLAIM" not in c_seg
    assert "均为非法动作" in proto
    # ② Human patch contract 由同一矩阵派生资格行
    prompt = RC.render_patch_prompt_v2([], {})
    assert f"kind=quote issues: {', '.join(matrix['quote'])} only." in prompt
    assert f"kind=citation issues: {', '.join(matrix['citation'])} only." in prompt
    # ③ applier 资格由矩阵驱动: citation+PARAPHRASE_CLAIM → INVALID_ACTION_FOR_CITATION
    from test_o7e_rca2_action_semantics import _LOG_SEARCH
    from final_validator import validate_final_candidate
    import repair_context as RC2
    cite_cand = ("引言测试正文，讨论《论语》的成书与流传。\n\n"
                 "书中另有说法，见【《论语》·八佾】。结尾一段正文保持结构完整。")
    v = validate_final_candidate(cite_cand, raw_tool_log=_LOG_SEARCH,
                                 fallback_log=[], language="zh")
    bundles = RC2.build_repair_issue_bundles(cite_cand, v, _LOG_SEARCH)
    ct = next(b for b in bundles if b["code"] == "UNVERIFIED_CITATION")
    patch = json.dumps({"patches": [
        {"issue_id": ct["issue_id"], "action": "PARAPHRASE_CLAIM",
         "replacement_text": "纯转述文本"}]}, ensure_ascii=False)
    new, errs = RC2.apply_main_agent_patches_v2(cite_cand, patch, [ct], {})
    assert new is None
    assert any("INVALID_ACTION_FOR_CITATION" in e for e in errs)
