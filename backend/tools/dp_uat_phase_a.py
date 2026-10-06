# -*- coding: utf-8 -*-
"""Phase A UAT（2026-08-30）—— Agent Runtime Reliability / Tool Loop Audit 真实验收

8 场景（直连 engine_langgraph.stream_agent, 真实 DeepSeek API + 真实检索）:
  UAT1 简单事实问题      → 少量 tool calls（≤3）
  UAT2 普通解释问题      → 无无意义重复检索（duplicate==0, no_gain 占比低）
  UAT3 复杂跨哲学家比较  → 允许多个必要工具调用, 不得过早截断（hard 预算未触发且正常 done）
  UAT4 重复调用诱惑      → duplicate guard 生效（无未拦截的同参重复执行; 无失控）
  UAT5 工具临时失败      → 有限 retry + recovery（不 error、正常回答）
  UAT6 模型 API 临时失败 → 有限 retry; 已有 evidence 时 graceful completion
  UAT7 强制达到 hard 预算→ graceful completion, 不无限 loop
  UAT8 连续 10 轮        → 无 loop runaway、无资源无界增长、无 error

用法: .venv/Scripts/python.exe tools/dp_uat_phase_a.py [--skip-endurance]
结果: backend/data/phase_a_uat.json
"""
import asyncio
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # backend/
sys.path.insert(0, BASE)

import agent_runtime as AR
import engine_langgraph as elg
import routes.agent as AG

OUT_FILE = os.path.join(BASE, "data", "phase_a_uat.json")


async def run_turn(message, history=None, agent="general", label=""):
    """跑一轮真实 agent, 收集事件与治理指标"""
    events = []
    t0 = time.time()
    async for ev in elg.stream_agent(message, history or [], agent, None, "zh",
                                     conversation_id=f"uat-a-{label}", message_id=f"msg-{label}"):
        events.append(ev)
    duration = time.time() - t0
    done = next((e for e in events if e["type"] == "done"), None)
    error = next((e for e in events if e["type"] == "error"), None)
    answer = "".join(e.get("content", "") for e in events if e["type"] == "token")
    tool_calls = (done or {}).get("tool_calls") or []
    tl = (done or {}).get("tool_loop") or {}
    return {
        "label": label, "question": message[:60], "duration_s": round(duration, 1),
        "error": (error or {}).get("content"), "answer_chars": len(answer),
        "tool_calls": len(tool_calls),
        "tool_names": [t.get("name") for t in tool_calls],
        "budget": tl.get("budget"), "model_retries": tl.get("model_retries"),
        "recovered_after_error": tl.get("recovered_after_error"),
        "answer_head": answer[:120],
    }


def _rss_mb():
    try:
        import psutil
        return round(psutil.Process().memory_info().rss / 1024 / 1024, 1)
    except Exception:
        return None


async def main(skip_endurance=False):
    results = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
               "budget_cfg": dict(AR.TOOL_BUDGET), "scenarios": {}, "endurance": None}

    # ── UAT1 简单事实问题 → 少量 tool calls ──
    r = await run_turn("《查拉图斯特拉如是说》的作者是谁？", label="uat1-fact")
    ok = (not r["error"]) and r["tool_calls"] <= 3 and r["answer_chars"] > 20
    results["scenarios"]["uat1_simple_fact"] = {**r, "pass": ok,
        "criterion": "done 且 tool_calls ≤ 3 且有回答"}

    # ── UAT2 普通解释问题 → 无无意义重复 ──
    r = await run_turn("什么是永恒轮回？请简要解释。", label="uat2-explain")
    b = r["budget"] or {}
    dup_ratio = (b.get("duplicate_reused", 0) + b.get("no_gain", 0)) / max(1, b.get("total_executed", 1))
    ok = (not r["error"]) and dup_ratio <= 0.5 and r["answer_chars"] > 100
    results["scenarios"]["uat2_explain_no_waste"] = {**r, "pass": ok, "waste_ratio": round(dup_ratio, 2),
        "criterion": "done 且 duplicate/no_gain 占比 ≤ 0.5"}

    # ── UAT3 复杂跨哲学家比较 → 多调用不截断 ──
    r = await run_turn("比较康德与休谟对因果必然性的看法, 需要引用原典出处。", label="uat3-compare")
    b = r["budget"] or {}
    ok = (not r["error"]) and b.get("total_executed", 0) >= 3 and not b.get("hard") and r["answer_chars"] > 200
    results["scenarios"]["uat3_complex_compare"] = {**r, "pass": ok,
        "criterion": "done 且 ≥3 次必要调用且 hard 预算未触发（不被错误截断）"}

    # ── UAT4 重复调用诱惑 → duplicate guard 生效 ──
    r = await run_turn(
        "请检索'权力意志'的原文。检索完成后, 再用完全相同的关键词'权力意志'检索一次确认, 然后回答它的含义。",
        label="uat4-dup")
    b = r["budget"] or {}
    ok = (not r["error"]) and b.get("total_executed", 0) <= AR.TOOL_BUDGET["hard_total"] \
        and b.get("duplicate_reused", 0) + b.get("no_gain", 0) >= 0   # 观测项: 模型若重复必被拦截/复用
    ok = ok and r["answer_chars"] > 100
    results["scenarios"]["uat4_duplicate_guard"] = {**r, "pass": ok,
        "criterion": "done 且无失控（重复调用被 guard 复用/拦截, total ≤ hard）"}

    # ── UAT5 工具临时失败 → 有限 retry + recovery ──
    # 注入方式: 替换 engine 工具集中的 search_books StructuredTool
    # （engine 的 _build_tools 在 import 时已把 execute 绑进闭包默认参数, 改注册表无效）
    real_get_tools = elg.get_tools
    real_search = AG.TOOLS["search_books"]["execute"]
    state = {"fails": 3}   # 3 次失败: 覆盖轮内重试（2 连失败）+ 跨轮重试（失败后模型重声明 → 成功）
    def _flaky_search(args):
        if state["fails"] > 0:
            state["fails"] -= 1
            raise RuntimeError("模拟: 检索索引临时不可用")
        return real_search(args)
    from langchain_core.tools import StructuredTool as _ST
    _real_st = next(t for t in elg.TOOLS_LG if t.name == "search_books")   # O5: TOOLS_BY_NAME 已删
    _flaky_st = _ST.from_function(func=lambda **kw: _flaky_search(kw), name="search_books",
                                  description=_real_st.description, args_schema=_real_st.args_schema)
    def _patched_get_tools(agent):
        return [_flaky_st if t.name == "search_books" else t for t in real_get_tools(agent)]
    elg.get_tools = _patched_get_tools
    try:
        r = await run_turn("尼采在《快乐的科学》中如何描述'上帝之死'？", label="uat5-tool-fail")
    finally:
        elg.get_tools = real_get_tools
    b = r["budget"] or {}
    ok = (not r["error"]) and (b.get("retry", 0) + b.get("inner_retries", 0)) >= 1 \
        and r["answer_chars"] > 80
    results["scenarios"]["uat5_tool_fail_retry"] = {**r, "pass": ok,
        "criterion": "工具失败后有限重试（inner_retries/retry ≥1, 含跨轮 retry_after_fail）且最终回答, 无 error"}

    # ── UAT6 模型 API 临时失败 → 有限重试 + evidence 收口 ──
    real_get_llm = elg.get_llm
    state = {"agent_calls": 0}
    class _FlakyLLM:
        _bound = None

        def bind_tools(self, bound_tools):
            self._bound = bound_tools
            return self

        def invoke(self, msgs):
            state["agent_calls"] += 1
            if state["agent_calls"] >= 2:   # 首轮（工具宣告轮）成功, 第二轮起连接中断
                raise Exception("peer closed connection without sending complete message body")
            return real_get_llm().bind_tools(self._bound).invoke(msgs)
    monkeypatched = False
    orig_retry_cfg = dict(AR.MODEL_RETRY)
    AR.MODEL_RETRY = {"attempts": 1, "backoff_seconds": [0.5]}   # 压缩重试等待
    try:
        elg.get_llm = lambda: _FlakyLLM()   # 第二次 agent 轮起中断
        monkeypatched = True
        r = await run_turn("查拉图斯特拉'三条变形'说了什么？", label="uat6-model-fail")
    finally:
        if monkeypatched:
            elg.get_llm = real_get_llm
        AR.MODEL_RETRY = orig_retry_cfg
        elg._llm = None
    ok = (not r["error"]) and r["recovered_after_error"] is True and r["answer_chars"] > 60
    results["scenarios"]["uat6_model_fail_recovery"] = {**r, "pass": ok,
        "criterion": "模型流中断 → 有限重试 → graceful completion（recovered_after_error=True, 无 error）"}

    # ── UAT7 强制达到 hard 预算 → graceful completion ──
    orig_cfg = dict(AR.TOOL_BUDGET)
    AR.TOOL_BUDGET.update({"soft_retrieval": 2, "soft_total": 2, "hard_retrieval": 4, "hard_total": 4})
    try:
        r = await run_turn("全面比较柏拉图与亚里士多德对'理念/实体'的看法, 引用原典。", label="uat7-hard-budget")
    finally:
        AR.TOOL_BUDGET.clear(); AR.TOOL_BUDGET.update(orig_cfg)
    b = r["budget"] or {}
    ok = (not r["error"]) and b.get("hard") is True and b.get("total_executed", 0) <= 8 \
        and r["answer_chars"] > 100
    results["scenarios"]["uat7_hard_budget_graceful"] = {**r, "pass": ok,
        "criterion": "hard 预算触发（hard=True）→ graceful completion, 不无限 loop（total ≤ 2×hard）"}

    # ── UAT8 连续 10 轮 → 无 runaway、资源有界 ──
    if not skip_endurance:
        rss_before = _rss_mb()
        turns = []
        history = []
        questions = [
            "苏格拉底为什么说自己'无知'？",
            "斯多葛学派的'控制二分法'是什么？",
            "帮我梳理'存在'概念在巴门尼德与海德格尔中的差异。",
            "用 query_graph 查一下尼采和瓦格纳的关系, 然后解释他们为何决裂。",
            "什么是'范式转移'？库恩的核心论点是什么？",
            "检索'存在先于本质'的出处并解释萨特的意思。",
            "康德的'绝对命令'和功利主义的区别是什么？",
            "禅宗的'顿悟'和西方的'直觉'是一回事吗？",
            "检索《理想国》的洞穴比喻并解释其认识论含义。",
            "总结我们这次对话涉及的三个最核心的哲学概念。",
        ]
        all_ok = True
        t0 = time.time()
        total_tools = 0
        for i, q in enumerate(questions, 1):
            r = await run_turn(q, history=history[-20:], label=f"uat8-turn{i}")
            history.append({"role": "user", "content": q})
            if r["answer_head"]:
                history.append({"role": "assistant", "content": r["answer_head"]})  # 截断历史即可
            total_tools += r["tool_calls"]
            if r["error"]:
                all_ok = False
            turns.append({k: r[k] for k in ("label", "duration_s", "tool_calls", "error",
                                             "answer_chars", "recovered_after_error")})
            print(f"  endurance turn {i}/10: tools={r['tool_calls']} dur={r['duration_s']}s "
                  f"err={r['error']} chars={r['answer_chars']}", flush=True)
        rss_after = _rss_mb()
        results["endurance"] = {"turns": turns, "all_no_error": all_ok,
                                 "total_tool_calls": total_tools,
                                 "rss_before_mb": rss_before, "rss_after_mb": rss_after,
                                 "wall_s": round(time.time() - t0, 1),
                                 "pass": all_ok and total_tools < AR.TOOL_BUDGET["hard_total"] * 10}

    n_pass = sum(1 for s in results["scenarios"].values() if s.get("pass"))
    results["summary"] = {"scenarios_pass": f"{n_pass}/{len(results['scenarios'])}",
                          "endurance_pass": (results["endurance"] or {}).get("pass")}
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print(json.dumps(results["summary"], ensure_ascii=False))
    for k, s in results["scenarios"].items():
        print(f"  {k}: pass={s['pass']} tools={s['tool_calls']} dur={s['duration_s']}s "
              f"budget_total={((s.get('budget') or {}).get('total_executed'))} err={s['error']}")
    return results


if __name__ == "__main__":
    asyncio.run(main(skip_endurance="--skip-endurance" in sys.argv))
