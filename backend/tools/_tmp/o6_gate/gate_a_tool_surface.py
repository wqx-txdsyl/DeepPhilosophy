# -*- coding: utf-8 -*-
"""O6 Gate A — §23 General/Nietzsche Tool Surface + specialized tools real smoke。
EVIDENCE-ONLY: 只调用生产工具 execute, 零修改。产出 runtime_tool_surface.json / .log"""
import asyncio
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, os.path.join(BASE, "backend"))
os.chdir(os.path.join(BASE, "backend"))

OUT = os.path.join(BASE, "backend", "tools", "_tmp", "o6_gate", "gate_a")
O0_REGISTRY = ["search_books", "get_book_detail", "get_chapter", "query_graph", "get_philosopher",
               "list_books", "write_essay", "generate_image", "get_school", "phti_test",
               "compare_views", "socratic_tutor", "philosopher_debate", "thought_experiment",
               "advisor_council", "paper_review", "analyze_argument", "concept_trace", "profile",
               "conceptual_map", "websearch", "query_database", "role_play", "essay_outline",
               "life_coach", "dialectic", "history_timeline", "confrontation", "school_arena",
               "agent_council"]

import engine_langgraph as EG  # noqa: E402
import agents as AGENTS        # noqa: E402
import routes.agent as AG      # noqa: E402


def dump_surface():
    g = [t.name for t in EG.get_tools("general")]
    n = [t.name for t in EG.get_tools("nietzsche")]
    rep = {
        "general_tools": sorted(g),
        "general_count": len(g),
        "general_duplicates": sorted({x for x in g if g.count(x) > 1}),
        "nietzsche_tools": sorted(n),
        "nietzsche_count": len(n),
        "nietzsche_duplicates": sorted({x for x in n if n.count(x) > 1}),
        "philo_extra_exposed_to_general": sorted(set(AGENTS.PHILO_EXTRA_TOOLS) & set(g)),
        "general_minus_o0_registry": sorted(set(g) - set(O0_REGISTRY)),
        "o0_registry_minus_general": sorted(set(O0_REGISTRY) - set(g)),
        "nietzsche_extra": sorted(set(n) - set(g)),
        "general_missing_shared": sorted(t.name for t in EG.TOOLS_LG if t.name not in set(g)),
        "philo_shared_def": sorted(AGENTS.PHILO_SHARED_TOOLS),
        "philo_extra_def": list(AGENTS.PHILO_EXTRA_TOOLS),
        "AG_TOOLS_count": len(AG.TOOLS),
    }
    return rep


SMOKE_TOOLS = {
    "compare_views": {"topic": "尼采与叔本华对痛苦的看法", "a": "尼采", "b": "叔本华"},
    "dialectic": {"topic": "自由与必然", "constraints": ""},
    "thought_experiment": {"topic": "忒修斯之船", "angle": "同一性"},
    "conceptual_map": {"topic": "存在主义", "style": "mindmap"},
    "analyze_argument": {"argument": "若一切皆被决定，则责任不存在；人有责任；所以并非一切皆被决定。"},
    "essay_outline": {"topic": "技术时代的人的处境", "points": ""},
    "socratic_tutor": {"topic": "什么是正义", "user_reply": ""},
}


def run_smoke():
    results = {}
    for name, args in SMOKE_TOOLS.items():
        meta = AG.TOOLS.get(name)
        if meta is None:
            results[name] = {"error": "tool missing from AG.TOOLS"}
            continue
        t0 = time.time()
        try:
            res = meta["execute"](dict(args))
            keys = sorted(res.keys()) if isinstance(res, dict) else f"type={type(res).__name__}"
            size = len(json.dumps(res, ensure_ascii=False, default=str))
            err = res.get("error") if isinstance(res, dict) else None
            results[name] = {"ok": not err, "error": err, "keys": keys,
                             "payload_chars": size, "duration_s": round(time.time() - t0, 1),
                             "preview": json.dumps(res, ensure_ascii=False, default=str)[:400]}
        except Exception as e:
            results[name] = {"ok": False, "error": f"{type(e).__name__}: {e}",
                             "duration_s": round(time.time() - t0, 1)}
    return results


# ── socratic engine-level scripted smoke（脚本化模型; 生产图路径）──
from langchain_core.language_models.chat_models import BaseChatModel  # noqa: E402


class ScriptedChat(BaseChatModel):
    """与 test_o2 harness 同风格（自写副本, 不动测试文件）"""
    script: list = []
    idx: int = 0

    @property
    def _llm_type(self):
        return "scripted-o6gate"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        from langchain_core.outputs import ChatResult, ChatGeneration
        msg = self.script[self.idx]
        self.idx += 1
        return ChatResult(generations=[ChatGeneration(message=msg)])

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        from langchain_core.messages import AIMessageChunk
        from langchain_core.outputs import ChatGenerationChunk
        msg = self.script[self.idx]
        self.idx += 1
        text = msg.content or ""
        for i in range(0, len(text), 12):
            yield ChatGenerationChunk(message=AIMessageChunk(content=text[i:i + 12]))
        for tc in (msg.tool_calls or []):
            yield ChatGenerationChunk(message=AIMessageChunk(
                content="",
                tool_call_chunks=[{"name": tc["name"],
                                   "args": json.dumps(tc.get("args") or {}, ensure_ascii=False),
                                   "id": tc.get("id"), "index": 0, "type": "tool_call_chunk"}]))


def socratic_scripted_smoke():
    """脚本化冒烟: 模型宣告 socratic_tutor → 工具返回单问题 → 模型发布只含该问题的回答。
    断言: 工具真实执行（生产 stub 工具不覆盖 socratic → 用真实 AG.TOOLS 执行器）,
    runtime 无强制路由, 最终回答一个实质问题。"""
    from langchain_core.messages import AIMessage
    # 生产工具集里 socratic_tutor 是真实工具——get_tools 走真实注册表;
    # 其余检索工具用 stub, socratic_tutor 保留真实 execute（结构化, 内部有 LLM——
    # 为 scripted 冒烟替换其 execute 为确定性单问题返回, 仅作用于本冒烟进程内））
    real_exec = AG.TOOLS["socratic_tutor"]["execute"]

    def stub_socratic(args):
        return {"next_question": "你说正义是强者的利益——那么强者认定的利益，会不会有错的时候？",
                "note": "scripted-smoke"}

    AG.TOOLS["socratic_tutor"]["execute"] = stub_socratic
    real_get_llm, real_get_tools = EG.get_llm, EG.get_tools
    _chat = ScriptedChat(script=[
        AIMessage(content="用户要求苏格拉底式追问，我先调用工具取一个问题。",
                  tool_calls=[{"name": "socratic_tutor", "args": {"topic": "正义"}, "id": "s1"}]),
        AIMessage(content="好问题——你说正义是强者的利益；那么强者认定的利益，会不会有错的时候？"),
    ])
    EG.get_llm = lambda: _chat
    # 重建 StructuredTool 列表以拾取 stub execute（生产 TOOLS_LG 构造路径原样调用）
    tools_lg = EG._build_tools()

    def _tools(agent):
        return tools_lg
    EG.get_tools = _tools

    def _no_hidden_llm(*a, **k):
        raise AssertionError("收口路径不得调用隐藏 LLM")
    real_llm_chat = AG.llm_chat
    AG.llm_chat = _no_hidden_llm

    async def _collect():
        evs = []
        async for ev in EG.stream_agent("只问我一个问题，不要直接给答案：什么是正义？",
                                        [], agent="general", language="zh"):
            evs.append(ev)
        return evs

    try:
        evs = asyncio.run(_collect())
    finally:
        EG.get_llm, EG.get_tools = real_get_llm, real_get_tools
        AG.TOOLS["socratic_tutor"]["execute"] = real_exec
        AG.llm_chat = real_llm_chat
    tools_fired = [e.get("name") for e in evs if e.get("type") == "tool"]
    answer = "".join(e.get("content", "") for e in evs if e.get("type") == "token")
    done = [e for e in evs if e.get("type") == "done"]
    return {
        "tools_fired": tools_fired,
        "answer": answer[:300],
        "question_count_heuristic": answer.count("？"),
        "validation_ok": done[0]["validation"]["result"]["ok"] if done else None,
        "initiated_by_all_main_agent": all(e.get("initiated_by") == "main_agent"
                                           for e in evs if e.get("type") == "tool_start"),
        "runtime_route_injection": any("必须" in str(e.get("content", "")) and e.get("initiated_by") == "runtime"
                                       for e in evs),
    }


def main():
    rep = {"surface": dump_surface()}
    print(json.dumps(rep["surface"], ensure_ascii=False, indent=1))
    rep["socratic_scripted_smoke"] = socratic_scripted_smoke()
    print("socratic scripted:", json.dumps(rep["socratic_scripted_smoke"], ensure_ascii=False)[:500])
    rep["specialized_smoke_real_api"] = run_smoke()
    for k, v in rep["specialized_smoke_real_api"].items():
        print(f"SMOKE {k}: ok={v.get('ok')} err={v.get('error')} keys={v.get('keys')} {v.get('duration_s')}s")
    with open(os.path.join(OUT, "runtime_tool_surface.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1, default=str)
    print("WROTE runtime_tool_surface.json")


if __name__ == "__main__":
    main()
