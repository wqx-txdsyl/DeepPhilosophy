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
