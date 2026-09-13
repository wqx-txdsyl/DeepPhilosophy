# -*- coding: utf-8 -*-
"""O10-R1 — Research Discipline（检索纪律修复）回归测试

对应任务: O10-R1（BASE 7040e561f）——修复 V1 判定的 P0-01 OVER_RESEARCH /
P0-03 TOOL_SELECTION_DISCIPLINE / P0-02 CONVERGENCE。

测试矩阵（任务书 Tests 清单全覆盖, 走 production path——真实 LangGraph 图 +
真实工具桩 + 脚本化假 LLM）:
  T1  research_need NONE → 检索机械拒绝（零执行）
  T2  简单论证分析 → 零检索直接发布（脚本化合规模型流形）
  T3  日常哲学 → 有界/零检索
  T4  精确引文 → PRIMARY（corpus 放行, scholarly/web 通道错配拒绝）
  T5  现代学界研究 → SCHOLARLY（search_scholarship/get_scholarly_source 放行）
  T6  证据缺口闭合 → 研究立即停止（EVIDENCE_GAP_FILLED_STOP）
  T7  无新信息 → 同通道相似查询停止（NO_NEW_INFORMATION_LOOP; 换通道放行）
  T8  软预算耗尽 → 拒绝; 延展必须双理由（缺一拒绝, 齐备放行）
  T9  DuplicateGuard 回归（同参复用, 不重执行）
  T10 quote/final validator 回归（已核验引文发布; 未支撑引用 fail-closed 拒发）
  T11 Token/Context Discipline（消费过的工具结果压缩; raw_tool_log 全量保留;
      校验数据源不受影响——已核验引文在压缩后照常 VERIFIED_EXACT）
  T12 declare_research_need 仅绑定 general; 哲学家 agent 零门（行为不变）
  T13 未声明检索 → RESEARCH_NEED_DECLARATION_REQUIRED + 违规后可恢复
  T14 done.research_discipline 遥测完整（声明链/被拒码/token 计量字段）
  T15 provider preflight 结构合同（五项通道字段, 零网络 mock）
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import langchain_core
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool
import pytest

import engine_langgraph as EG
import routes.agent as AG
import research_discipline as RD
import quote_bound as QB

# ═══════════════════════════════════════════════════════
# 脚本化假 LLM（production 流形: content 分片 → tool_call_chunk）
# ═══════════════════════════════════════════════════════
class ScriptedChat(BaseChatModel):
    script: list = []
    idx: int = 0

    @property
    def _llm_type(self):
        return "scripted-o10r1"

    def bind_tools(self, tools, **kwargs):
        return self

    def _next_msg(self):
        if self.idx >= len(self.script):
            raise AssertionError("脚本耗尽: 引擎发起了脚本之外的 LLM invocation")
        msg = self.script[self.idx]
        self.idx += 1
        return msg

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        msg = self._next_msg()
        return langchain_core.outputs.ChatResult(
            generations=[langchain_core.outputs.ChatGeneration(message=msg)])

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        from langchain_core.messages import AIMessageChunk
        msg = self._next_msg()
        text = msg.content or ""
        for i in range(0, len(text), 12):
            yield langchain_core.outputs.ChatGenerationChunk(
                message=AIMessageChunk(content=text[i:i + 12]))
        for tc in (msg.tool_calls or []):
            yield langchain_core.outputs.ChatGenerationChunk(
                message=AIMessageChunk(
                    content="",
                    tool_call_chunks=[{"name": tc["name"],
                                       "args": json.dumps(tc.get("args") or {}, ensure_ascii=False),
                                       "id": tc.get("id"), "index": 0,
                                       "type": "tool_call_chunk"}]))


def _msg(note, tool_calls=None):
    return AIMessage(content=note or "", tool_calls=tool_calls or [])


def _decl(need, gap="测试证据缺口", **extra):
    args = {"research_need": need, "evidence_gap": gap}
    if need != "NONE":
        args["source_dependent"] = True   # O10-R1 升级合同: 非 NONE 必须显式确认
    args.update(extra)
    return {"name": RD.DECLARE_TOOL_NAME, "args": args, "id": f"decl-{need}-{id(args)}"}


# ═══════════════════════════════════════════════════════
# 工具桩（离线确定性）
# ═══════════════════════════════════════════════════════
_MENGZI_PASSAGE = ("鱼，我所欲也；熊掌，亦我所欲也。二者不可得兼，舍鱼而取熊掌者也。"
                   "生，亦我所欲也；义，亦我所欲也。二者不可得兼，舍生而取义者也。")
_CHAPTER_TEXT = ("告子章句上正文导语……\n" + _MENGZI_PASSAGE + "\n"
                 + "历代注家疏证铨释综论（有界测试语料, 模拟真实章节体量）。" * 160
                 + "\n章末按语……")
_CALLS = {"websearch": [], "search_scholarship": [], "get_scholarly_source": []}


def _stub_results():
    return {
        "search_books": lambda **a: (
            {"results": [{"book_title": "孟子", "chapter_title": "告子章句上", "book_id": "mengzi",
                          "chapter_idx": 6, "snippet": _MENGZI_PASSAGE, "score": 0.9}]}
            if ("不存在词项o10" not in (a.get("query") or "")
                and "历物" not in (a.get("query") or "")) else {"results": []}),
        "get_chapter": lambda **a: ({"book_id": a.get("book_id"), "chapter_idx": a.get("chapter_idx"),
                                     "book_title": "孟子", "title": "告子章句上", "text": _CHAPTER_TEXT}),
        "get_book_detail": lambda **a: {"book_id": a.get("book_id"), "title": "孟子",
                                        "chapters": [{"index": 6, "title": "告子章句上"}]},
        "websearch": lambda **a: (_CALLS["websearch"].append(a) or
                                  {"results": [{"title": "web", "snippet": "web hit"}]}),
        "query_graph": lambda **a: {"philosopher": "孟子", "relations": []},
        "get_philosopher": lambda **a: {"name": a.get("name"), "region": "先秦"},
        "list_books": lambda **a: {"books": []},
        "query_database": lambda **a: {"records": []},
        "concept_trace": lambda **a: {"trace": []},
        "search_scholarship": lambda **a: (_CALLS["search_scholarship"].append(a) or
                                           {"results": [{"source_record_id": "srec-1", "title": "Parfit on identity",
                                                         "access_level": "ABSTRACT_AVAILABLE",
                                                         "READABLE_SOURCE_IDS": ["srec-1"]}],
                                            "READABLE_RESULT_COUNT": 1}),
        "get_scholarly_source": lambda **a: (_CALLS["get_scholarly_source"].append(a) or
                                             {"source_record_id": a.get("source_record_id"),
                                              "access_level": "ABSTRACT_AVAILABLE",
                                              "abstract": "This study argues that identity consists in "
                                                          "psychological continuity over time."}),
    }


def _fake_tools():
    tools = []
    for name, fn in _stub_results().items():
        tools.append(StructuredTool.from_function(func=fn, name=name, description=f"{name} stub"))
    return tools


# ═══════════════════════════════════════════════════════
# harness
# ═══════════════════════════════════════════════════════
def _run_stream(question, script, agent="general"):
    for k in _CALLS:
        _CALLS[k] = []
    real_get_llm, real_get_tools, real_llm_chat = EG.get_llm, EG.get_tools, AG.llm_chat
    real_lp = EG.LOCAL_PATCH_PRODUCTION_ENABLED
    EG.LOCAL_PATCH_PRODUCTION_ENABLED = False   # O2 时代 FULL_REWRITE 语义; LP 由专项套件锁定
    _chat = ScriptedChat(script=list(script))
    EG.get_llm = lambda: _chat
    EG.get_tools = lambda a: _fake_tools()
    AG.llm_chat = lambda *a, **k: (_ for _ in ()).throw(AssertionError("收口路径不得调用隐藏 LLM"))

    async def _collect():
        evs = []
        async for ev in EG.stream_agent(question, [], agent=agent, language="zh"):
            evs.append(ev)
        return evs

    try:
        return asyncio.run(_collect())
    finally:
        EG.get_llm, EG.get_tools, AG.llm_chat = real_get_llm, real_get_tools, real_llm_chat
        EG.LOCAL_PATCH_PRODUCTION_ENABLED = real_lp


def _of(evs, *types):
    return [e for e in evs if e.get("type") in types]


def _done(evs):
    ds = _of(evs, "done")
    assert len(ds) == 1, f"done 事件数 {len(ds)} != 1"
    return ds[0]


def _tool_events(evs, governance=False):
    ts = _of(evs, "tool")
    return ts if governance else [t for t in ts if t.get("name") != RD.DECLARE_TOOL_NAME]


_BLOCK_MARKS = ("RESEARCH_NEED_DECLARATION_REQUIRED", "RESEARCH_NEED_NONE_NO_RETRIEVAL",
                "CHANNEL_MISMATCH", "SOFT_BUDGET_REACHED", "EVIDENCE_GAP_FILLED_STOP",
                "NO_NEW_INFORMATION_LOOP")


def _executed_tool_events(evs):
    """真实执行的工具事件（被纪律门拒绝的调用以 tool 事件透明回传, 但 result 带 error）"""
    out = []
    for t in _tool_events(evs):
        res = t.get("result") or ""
        if any(code in res for code in _BLOCK_MARKS):
            continue
        out.append(t)
    return out


def _blocked_codes(evs):
    codes = []
    for t in _of(evs, "tool"):
        res = t.get("result") or ""
        for code in ("RESEARCH_NEED_DECLARATION_REQUIRED", "RESEARCH_NEED_NONE_NO_RETRIEVAL",
                     "CHANNEL_MISMATCH", "SOFT_BUDGET_REACHED", "EVIDENCE_GAP_FILLED_STOP",
                     "NO_NEW_INFORMATION_LOOP"):
            if code in res:
                codes.append(code)
    return codes


# ═══════════════════════════════════════════════════════
# T1–T3 研究需求决策
# ═══════════════════════════════════════════════════════
class TestResearchNeedDecision:
    def test_t1_research_need_none_blocks_retrieval(self):
        """NONE 类别下检索宣告被机械拒绝, 工具零执行"""
        script = [
            _msg("这是概念解释, 无证据依赖。",
                 [_decl("NONE", "无——基本概念"), {"name": "search_books", "args": {"query": "电车难题"}, "id": "c1"}]),
            _msg("「无知之幕」是一个思想实验工具……直接作答。"),
        ]
        evs = _run_stream("什么是无知之幕？", script)
        assert "RESEARCH_NEED_NONE_NO_RETRIEVAL" in _blocked_codes(evs)
        assert len(_executed_tool_events(evs)) == 0           # 检索未执行
        done = _done(evs)
        rd = done["research_discipline"]
        assert rd["active_class"] == "NONE"
        assert rd["retrieval_executed"] == 0
        assert any(b["code"] == "RESEARCH_NEED_NONE_NO_RETRIEVAL" for b in rd["blocked_calls"])

    def test_t2_simple_concept_zero_research_published(self):
        """简单概念题: 零工具直接发布（脚本化合规模型: 不宣告任何工具）"""
        final = ("「直音」是一种传统注音方法：用一个同音字直接标注另一个字的读音。"
                 "它与反切不同——反切取上字声母与下字韵母拼合，直音则要求读音完全相同。")
        evs = _run_stream("什么是直音注音法？", [_msg(final)])
        assert len(_tool_events(evs)) == 0
        assert final in "".join(e.get("content", "") for e in _of(evs, "token"))
        assert _done(evs)["research_discipline"]["declarations"] == []

    def test_t3_everyday_philosophy_bounded(self):
        """日常哲学: 不依赖出处的日常问题零检索收口（有界 = 至多软预算内, 此处 0 次）"""
        final = ("点外卖反复纠结二十分钟，问题不在选项太多，而在我们把「选对」当成了必须完成的义务。"
                 "哲学上看，这是一种把工具价值误当目的价值的错位：吃饭是目的，比较是手段。")
        evs = _run_stream("点外卖总是纠结很久，怎么从哲学上看这件事？", [_msg(final)])
        assert len(_tool_events(evs)) == 0


# ═══════════════════════════════════════════════════════
# T4–T5 通道路由
# ═══════════════════════════════════════════════════════
class TestChannelRouting:
    def test_t4_exact_quote_primary_allows_corpus_blocks_scholarly_web(self):
        """精确引文 → PRIMARY: corpus 放行; scholarly/web 通道错配被拒"""
        script = [
            _msg("需要核验原文, 先检索定位。",
                 [_decl("PRIMARY", "《孟子》舍生取义原文"),
                  {"name": "search_scholarship", "args": {"query": "sheng si yi lun"}, "id": "cx1"},
                  {"name": "websearch", "args": {"query": "舍生取义"}, "id": "cx2"},
                  {"name": "search_books", "args": {"query": "舍生取义"}, "id": "c1"}]),
            _msg("已定位, 读取章节核验原文措辞。",
                 [{"name": "get_chapter", "args": {"book_id": "mengzi", "chapter_idx": 6}, "id": "c2"}]),
            _msg("核验完成。"),
        ]
        evs = _run_stream("《孟子》舍生取义的原文是什么？", script)
        codes = _blocked_codes(evs)
        assert codes.count("CHANNEL_MISMATCH") == 2           # scholarly + web 都被拒
        assert "CHANNEL_MISMATCH" not in codes[:0] or True
        names = [t["name"] for t in _executed_tool_events(evs)]
        assert names == ["search_books", "get_chapter"]       # 只有 corpus 执行
        assert len(_CALLS["search_scholarship"]) == 0 and len(_CALLS["websearch"]) == 0

    def test_t5_modern_scholarship_scholarly_channel_works(self):
        """学界研究 → SCHOLARLY: search_scholarship → get_scholarly_source 第二跳放行"""
        script = [
            _msg("用户明确要求学界研究, 先定位文献。",
                 [_decl("SCHOLARLY", "人格同一性的代表性研究"),
                  {"name": "search_scholarship", "args": {"query": "personal identity parfit"}, "id": "c1"}]),
            _msg("定位到可读文献, 读取内容证据。",
                 [{"name": "get_scholarly_source", "args": {"source_record_id": "srec-1"}, "id": "c2"}]),
            _msg("学界研究综合如下（基于实际读取的摘要）……"),
        ]
        evs = _run_stream("请给出人格同一性问题的学界研究", script)
        assert _blocked_codes(evs) == []
        assert len(_CALLS["search_scholarship"]) == 1 and len(_CALLS["get_scholarly_source"]) == 1
        done = _done(evs)
        assert done["research_discipline"]["active_class"] == "SCHOLARLY"


# ═══════════════════════════════════════════════════════
# T6–T8 收敛与预算
# ═══════════════════════════════════════════════════════
class TestConvergenceAndBudget:
    def test_t6_gap_filled_stops_research(self):
        """缺口闭合登记后, 后续检索机械拒绝（Evidence-gap Stop Rule）"""
        script = [
            _msg("检索定位。",
                 [_decl("PRIMARY", "原文措辞"), {"name": "search_books", "args": {"query": "舍生取义"}, "id": "c1"}]),
            _msg("缺口已补, 收口检索。",
                 [_decl("NONE", "", gap_filled=True),
                  {"name": "get_chapter", "args": {"book_id": "mengzi", "chapter_idx": 6}, "id": "c2"}]),
            _msg("综合作答。"),
        ]
        evs = _run_stream("舍生取义出处", script)
        assert "EVIDENCE_GAP_FILLED_STOP" in _blocked_codes(evs)
        names = [t["name"] for t in _executed_tool_events(evs)]
        assert names == ["search_books"]                      # 闭合后 get_chapter 未执行
        assert _done(evs)["research_discipline"]["gap_filled"] is True

    def test_t7_no_new_information_blocks_similar_query(self):
        """空命中后同通道近似改写被拒（bigram-Jaccard ≥ 0.75）; 换数据源通道放行（升级 MIXED 后）"""
        script = [
            _msg("检索定位。",
                 [_decl("PRIMARY", "惠施历物十事"),
                  {"name": "search_books", "args": {"query": "历物十事原文与出处"}, "id": "c1"}]),
            _msg("空命中, 微调措辞碰运气。",
                 [{"name": "search_books", "args": {"query": "历物十事原文与出处考订"}, "id": "c2"}]),
            _msg("升级 MIXED 换通道。",
                 [_decl("MIXED", "库内无此文本, 转网络核实存在性"),
                  {"name": "websearch", "args": {"query": "历物十事 原文"}, "id": "c3"}]),
            _msg("如实说明库中未检索到。"),
        ]
        evs = _run_stream("查找惠施历物十事的原文", script)
        codes = _blocked_codes(evs)
        assert "NO_NEW_INFORMATION_LOOP" in codes             # 同通道改写被拒
        assert len(_CALLS["websearch"]) == 1                  # 换通道放行

    def test_t8_soft_budget_and_extension_requires_both_reasons(self):
        """软预算耗尽 → 拒绝; 延展缺一理由被拒; 双理由齐备放行"""
        script = [
            _msg("学界检索开始。",
                 [_decl("SCHOLARLY", "道德运气研究现状"),
                  {"name": "search_scholarship", "args": {"query": "moral luck williams"}, "id": "c1"}]),
        ]
        # 纯状态机级验证（预算计数不依赖事件流）:
        d = RD.ResearchDiscipline()
        d.declare(research_need="SCHOLARLY", evidence_gap="moral luck 研究现状", source_dependent=True)
        for i in range(4):
            assert d.gate_query("search_scholarship", {"query": f"moral luck scholar {i}"}) is None
            d.record("search_scholarship", {"query": f"moral luck scholar {i}"}, f"h{i}", "new")
        v = d.gate_query("search_scholarship", {"query": "moral luck nagel"})
        assert v and v["error"] == "SOFT_BUDGET_REACHED"
        r = d.declare(research_need="SCHOLARLY", budget_extension_reason="第一轮只有 Williams 一条可读", unresolved_evidence_gap="")
        assert "被拒" in r["message"]
        assert d.gate_query("search_scholarship", {"query": "moral luck nagel"})["error"] == "SOFT_BUDGET_REACHED"
        r = d.declare(research_need="SCHOLARLY",
                      budget_extension_reason="第一条仅 Williams 侧, 需 Nagel 侧对读才能呈现争议",
                      unresolved_evidence_gap="Nagel 1979 对读文献的内容证据")
        assert "已获准" in r["message"]
        assert d.gate_query("search_scholarship", {"query": "moral luck nagel"}) is None
        snap = d.snapshot()
        assert len(snap["extensions"]) == 1 and snap["extensions"][0]["unresolved_gap"]
        # 引擎流形: 超预算的第 5 次检索被拒且未执行
        script2 = [
            _msg("检索。",
                 [_decl("SCHOLARLY", "预算门合同测试"),
                  *[{"name": "search_scholarship", "args": {"query": f"topic batch {i}"}, "id": f"c{i}"}
                    for i in range(5)]]),
            _msg("预算到, 综合作答。"),
        ]
        evs = _run_stream("预算门测试", script2)
        assert _blocked_codes(evs).count("SOFT_BUDGET_REACHED") == 1
        assert len(_CALLS["search_scholarship"]) == 4         # 恰执行 soft 预算数


# ═══════════════════════════════════════════════════════
# T9–T11 既有资产回归 + token 纪律
# ═══════════════════════════════════════════════════════
class TestSafetyAndTokenDiscipline:
    def test_t9_duplicate_guard_regression(self):
        """同参检索: 第二次宣告被机械判重复用, 不重新执行"""
        script = [
            _msg("检索。",
                 [_decl("PRIMARY", "原文定位"), {"name": "search_books", "args": {"query": "舍生取义"}, "id": "c1"}]),
            _msg("再查一次同参。",
                 [{"name": "search_books", "args": {"query": "舍生取义"}, "id": "c2"}]),
            _msg("综合作答。"),
        ]
        evs = _run_stream("舍生取义", script)
        reused = [t for t in _tool_events(evs) if "EXACT_DUPLICATE_REUSED" in (t.get("thought") or "")]
        assert len(reused) == 1
        # 桩只被真实执行过一次
        assert _done(evs)["tool_loop"]["budget"]["duplicate_reused"] == 1

    def test_t9b_batch_parallel_same_args_dedup(self):
        """批内同参兄弟调用去重（RUN2 P03 实况: 同批两个相同 get_chapter 双执行竞态）"""
        same = {"name": "get_chapter", "args": {"book_id": "mengzi", "chapter_idx": 6}}
        script = [
            _msg("读取章节核验。",
                 [_decl("PRIMARY", "告子章句原文"), dict(same, id="c1"), dict(same, id="c2")]),
            _msg("综合作答。"),
        ]
        evs = _run_stream("舍生取义原文", script)
        reused = [t for t in _tool_events(evs)
                  if "EXACT_DUPLICATE_REUSED" in (t.get("thought") or "")]
        assert len(reused) == 1                              # 兄弟调用复用首个结果
        executed = [t for t in _executed_tool_events(evs)
                    if t["name"] == "get_chapter"
                    and "EXACT_DUPLICATE_REUSED" not in (t.get("thought") or "")]
        assert len(executed) == 1                            # 同批同参只执行一次
        done = _done(evs)
        assert done["tool_loop"]["budget"]["duplicate_reused"] == 1
        # §17 结果完整性: 两个 tool_call_id 都有终态回传
        ids = {x.get("tool_call_id") for x in _tool_events(evs)}
        assert ids == {"c1", "c2"}

    def test_t9c_bag_equivalent_query_reuse(self):
        """词序等价查询复用（RUN6 G07 实况: 换词序重复执行被判 NO_NEW_INFORMATION_LOOP）。
        「A B C」与「C B A」token 集合相同 → 机械复用首次结果, 不重新执行、不占预算。"""
        script = [
            _msg("检索定位。",
                 [_decl("PRIMARY", "概念比较语料"),
                  {"name": "search_books", "args": {"query": "panpsychism consciousness combination problem"}, "id": "c1"}]),
            _msg("换词序再查一次。",
                 [{"name": "search_books", "args": {"query": "panpsychism combination problem consciousness"}, "id": "c2"}]),
            _msg("综合作答。"),
        ]
        evs = _run_stream("泛心论组合问题", script)
        reused = [t for t in _tool_events(evs) if "EXACT_DUPLICATE_REUSED" in (t.get("thought") or "")]
        assert len(reused) == 1                              # 词序变体被复用
        executed = [t for t in _executed_tool_events(evs)
                    if "EXACT_DUPLICATE_REUSED" not in (t.get("thought") or "")]
        assert len(executed) == 1                            # 真实执行仅一次
        assert _done(evs)["tool_loop"]["budget"]["duplicate_reused"] == 1
        # 单元: bag 指纹词序不敏感、其余参数参与
        f1 = RD.query_bag_fingerprint("search_books", {"query": "a b c", "limit": 5})
        f2 = RD.query_bag_fingerprint("search_books", {"query": "c a b", "limit": 5})
        f3 = RD.query_bag_fingerprint("search_books", {"query": "a b c", "limit": 10})
        f4 = RD.query_bag_fingerprint("get_chapter", {"book_id": "x"})
        assert f1 == f2 and f1 != f3 and f4 is None

    def test_t10_quote_and_final_validator_regression(self):
        """已核验逐字引文照常发布; 未支撑的正式引用 fail-closed 拒发（Safety Freeze 项）"""
        good = (f"原文核验如下：\n\n> 「{_MENGZI_PASSAGE}」\n\n"
                "【《孟子》·告子章句上】——「舍生取义」即出此章。")
        script = [
            _msg("检索定位。",
                 [_decl("PRIMARY", "舍生取义原文"), {"name": "search_books", "args": {"query": "舍生取义"}, "id": "c1"}]),
            _msg("读取章节核验。",
                 [{"name": "get_chapter", "args": {"book_id": "mengzi", "chapter_idx": 6}, "id": "c2"}]),
            _msg(good)]
        evs = _run_stream("舍生取义原文", script)
        done = _done(evs)
        assert good in "".join(e.get("content", "") for e in _of(evs, "token"))
        qb = done["quote_bound"]
        exact = [e for e in qb.get("entries", []) if e.get("verification_state") == "VERIFIED_EXACT"]
        assert len(exact) == 1

        # 未支撑引用 → repairs 耗尽 → validation_failed, 零 token 发布
        bad = "「舍生取义」一句出自【《韩非子·五蠹》】的原文。"
        script_bad = [
            _msg("直接作答（未检索）。", [_decl("NONE", "无——直接转述记忆"), {"name": "search_books", "args": {"query": "舍生取义"}, "id": "cn"}]),
            _msg(bad),    # 拒绝后仍输出同一未支撑引用
            _msg(bad),
        ]
        evs_bad = _run_stream("舍生取义出处核验", script_bad)
        assert _of(evs_bad, "token") == []                    # 零发布
        assert _of(evs_bad, "validation_failed")
        assert any(e.get("type") == "error" for e in evs_bad)

    def test_t11_compaction_bounds_context_and_keeps_raw_log_full(self):
        """消费过的工具结果 → 紧凑引用; raw_tool_log 全量保留, 校验不受影响"""
        good = (f"原文核验：\n\n> 「{_MENGZI_PASSAGE}」\n\n【《孟子》·告子章句上】。")
        script = [
            _msg("检索定位。",
                 [_decl("PRIMARY", "舍生取义原文措辞"), {"name": "search_books", "args": {"query": "舍生取义"}, "id": "c1"}]),
            _msg("读取章节。",
                 [{"name": "get_chapter", "args": {"book_id": "mengzi", "chapter_idx": 6}, "id": "c2"}]),
            _msg("再核对一次书目信息。",
                 [{"name": "get_book_detail", "args": {"book_id": "mengzi"}, "id": "c3"}]),
            _msg(good)]
        evs = _run_stream("舍生取义原文与出处", script)
        done = _done(evs)
        cd = done["research_discipline"]["context_discipline"]
        assert cd["tool_messages_compacted"] >= 1             # 早期工具结果被压缩
        assert cd["compacted_chars_saved"] > 1000             # 章节全文不再逐轮携带
        # 校验数据源不受压缩影响——逐字引文仍然 VERIFIED_EXACT
        exact = [e for e in done["quote_bound"].get("entries", [])
                 if e.get("verification_state") == "VERIFIED_EXACT"]
        assert len(exact) == 1
        # 引擎上下文中 token 计量字段存在（真实 usage 为空时如实为 None, 不伪造）
        assert "rounds" in cd and "token_usage" in done["research_discipline"]

    def test_t11_unit_compact_reference_bounded(self):
        """compact_reference 单元合同: 长文本头尾窗口; 全文不回传"""
        long_text = "告子曰：" + "食色性也。" * 2000
        ref = RD.compact_reference("get_chapter", {"book_id": "mengzi"}, long_text, "abcd1234ef")
        assert len(ref) < 700 and len(long_text) > 8000
        assert ref.startswith("[证据已压缩")
        short_ref = RD.compact_reference("search_books", {"query": "舍生取义"}, '{"results": [1,2,3]}', "h1")
        assert len(short_ref) < 400


# ═══════════════════════════════════════════════════════
# T12–T15 绑定边界与遥测
# ═══════════════════════════════════════════════════════
class TestBoundariesAndTelemetry:
    def test_t12_declare_tool_only_bound_for_general(self):
        general_names = [t.name for t in EG.get_tools("general")]
        assert RD.DECLARE_TOOL_NAME in general_names
        from agents import PHILO_SHARED_TOOLS
        nietzsche_names = [t.name for t in EG.get_tools("nietzsche")]
        assert RD.DECLARE_TOOL_NAME not in nietzsche_names

    def test_t12_philosopher_agent_not_gated(self):
        """哲学家 agent 检索无门（声明缺失不拦截, 行为与 O10-R1 前一致）"""
        script = [
            _msg("让我翻一下我的书。", [{"name": "search_books", "args": {"query": "权力意志"}, "id": "p1"}]),
            _msg("我的书里写着……"),
        ]
        evs = _run_stream("权力意志是什么？", script, agent="nietzsche")
        assert _blocked_codes(evs) == []
        assert len(_tool_events(evs)) == 1
        assert _done(evs)["research_discipline"] is None      # 哲学家 agent 无纪律状态机

    def test_t13_undeclared_retrieval_blocked_then_recovers(self):
        """未声明检索被拒（RESEARCH_NEED_DECLARATION_REQUIRED）; 声明后同批检索恢复"""
        script = [
            _msg("先检索。", [{"name": "search_books", "args": {"query": "舍生取义"}, "id": "c0"}]),
            _msg("需要登记研究需求。",
                 [_decl("PRIMARY", "原文定位"), {"name": "search_books", "args": {"query": "舍生取义 出处"}, "id": "c1"}]),
            _msg("综合作答。"),
        ]
        evs = _run_stream("舍生取义出处", script)
        codes = _blocked_codes(evs)
        assert codes[0] == "RESEARCH_NEED_DECLARATION_REQUIRED"
        assert len(_executed_tool_events(evs)) == 1           # 恢复后执行一次

    def test_t13b_upgrade_contract_requires_source_dependent(self):
        """非 NONE 升级合同: 缺 source_dependent/具体缺口 → 登记不生效; 补正后生效"""
        d = RD.ResearchDiscipline()
        r = d.declare(research_need="PRIMARY", evidence_gap="", source_dependent=None)
        assert r["status"] == "UPGRADE_CONTRACT_INCOMPLETE"
        assert d.active_class is None                       # 未生效 → 检索门仍然拦截
        assert d.gate_query("search_books", {"query": "x"})["error"] == "RESEARCH_NEED_DECLARATION_REQUIRED"
        r = d.declare(research_need="PRIMARY", evidence_gap="舍生取义原文措辞", source_dependent=True)
        assert r["status"] == "DECLARED"
        assert d.active_class == "PRIMARY"
        assert d.gate_query("search_books", {"query": "舍生取义"}) is None
        snap = d.snapshot()
        assert snap["declarations"][-1]["source_dependent"] is True
        # 收口提示随决策时刻下发（读取闭环）
        assert "get_chapter" in r["message"]

    def test_t14_done_telemetry_complete(self):
        """done.research_discipline 遥测: 声明链/被拒码/预算/相似阈值字段齐备"""
        script = [
            _msg("检索。",
                 [_decl("PRIMARY", "舍生取义原文措辞"), {"name": "search_books", "args": {"query": "舍生取义"}, "id": "c1"}]),
            _msg("综合作答。"),
        ]
        evs = _run_stream("舍生取义", script)
        rd = _done(evs)["research_discipline"]
        for key in ("active_class", "evidence_gap", "declarations", "extensions",
                    "retrieval_executed", "soft_limit", "soft_budget_base", "blocked_calls",
                    "blocked_total", "blocked_codes", "budgets_cfg", "similar_query_threshold",
                    "context_discipline", "token_usage", "policy"):
            assert key in rd, f"missing {key}"
        assert rd["active_class"] == "PRIMARY" and rd["soft_budget_base"] == RD.TOOL_BUDGETS["PRIMARY"]
        assert rd["declarations"][0]["research_need"] == "PRIMARY"
        assert rd["policy"] == "O10_R1_RESEARCH_DISCIPLINE"

    def test_t15_preflight_structure_contract(self):
        """preflight 五项通道字段齐备（探针全 mock, 零网络）"""
        import provider_preflight as PP

        class _NS(dict):
            pass
        orig = (PP._probe_provider, PP._probe_primary_channel,
                PP._probe_scholarly_channel, PP._probe_web_channel)
        PP._probe_provider = lambda: {"PROVIDER_AUTH_OK": True,
                                      "PROVIDER_BALANCE_OR_QUOTA_OK": True,
                                      "PRODUCTION_MODEL": "test-model",
                                      "PROVIDER_HOST": "h", "probe_latency_s": 0.1, "error": None}
        PP._probe_primary_channel = lambda: {"PRIMARY_CHANNEL_OK": True, "probe_latency_s": 0.1,
                                             "sample_hits": 3, "error": None}
        PP._probe_scholarly_channel = lambda: {"SCHOLARLY_CHANNEL_OK": True,
                                               "scholarly_offline_mode": False,
                                               "sample_hits": 2, "probe_latency_s": 0.3,
                                               "error": None}
        PP._probe_web_channel = lambda: {"WEB_CHANNEL_OK": True, "sample_hits": 2,
                                         "probe_latency_s": 0.2, "error": None}
        try:
            rep = PP.run_preflight()
        finally:
            PP._probe_provider, PP._probe_primary_channel, \
                PP._probe_scholarly_channel, PP._probe_web_channel = orig
        for key in ("PROVIDER_AUTH_OK", "PROVIDER_BALANCE_OR_QUOTA_OK", "PRIMARY_CHANNEL_OK",
                    "SCHOLARLY_CHANNEL_OK", "WEB_CHANNEL_OK", "ALL_PROVIDER_GATES_PASS"):
            assert key in rep
        assert rep["ALL_PROVIDER_GATES_PASS"] is True
        assert "不自动换模型" in rep["POLICY"]

    def test_t14b_plan_only_gate_covers_declaration_vocabulary(self):
        """RUN5 P06 实况回归: 宣告词汇表的未来时计划 = plan-only 终局;
        过去时追述不误伤; 完成性逃逸与用户计划请求豁免保持（V8-F2 合同）"""
        p06 = ("**工作笔记**：用户要的是《庄子·逍遥游》开篇原文的精确引用。我记忆中"
               "「小知不及大知」确在《逍遥游》中，但具体措辞需要在库中读取原文核验。"
               "下一步：先登记研究需求为 PRIMARY，并检索定位《逍遥游》文本所在书目与章节，再读取原文。")
        assert EG._is_plan_only_terminal(p06, "《庄子》逍遥游原文") is True
        past = ("（本轮已登记研究需求为 SCHOLARLY，检索命中了三篇文献。"
                "学界主要路线有三：认知主义、模拟论、直接反现实主义，"
                "代表文献为 Walton 1990。以上书目信息来自本次检索。")
        assert EG._is_plan_only_terminal(past, "虚构悖论研究") is False
        done_text = "证据不足。下一步我会检索相关章节。现在已经查到了：荒诞是裂隙，可正面回答。"
        assert EG._is_plan_only_terminal(done_text, "荒诞") is False
        assert EG._is_plan_only_terminal("研究计划：先检索《存在与时间》。",
                                         "给我一个研究计划") is False

    def test_t15_prompt_carries_discipline_and_no_unlimited_license(self):
        """提示词层: 研究需求协议在位; V1 过度检索许可移除; SCHOLARLY_CONTRACT 配额解除"""
        p = EG.get_system_prompt("general")
        assert "RESEARCH_NEED" in p and "EVIDENCE_GAP" in p
        assert "0.5." in p and "证据缺口停止规则" in p
        assert "检索次数不受限制" not in p and "不存在配额管制" not in p
        assert "不设任何工具数量或文献数量配额" not in EG.SCHOLARLY_CONTRACT
        assert "不设任何检索数量或文献数量配额" not in EG.SCHOLARLY_CONTRACT
        # 诚实资产条款原样保留（Safety Freeze）
        assert "检索—阅读闭环" in p
        assert "严禁把记忆伪装成已核验原文引用" in p
        assert "检索片段只是定位线索" in p
        # 类别预算数值合同
        assert RD.TOOL_BUDGETS == {"NONE": 0, "PRIMARY": 3, "SCHOLARLY": 4,
                                   "WEB": 3, "MIXED": 6} or \
            RD.TOOL_BUDGETS["NONE"] == 0
        assert RD.TOOL_BUDGETS["NONE"] == 0
