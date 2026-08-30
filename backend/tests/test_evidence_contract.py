# -*- coding: utf-8 -*-
"""Evidence Contract（Phase 3）用例——检索≠已用 / claim→evidence 绑定 / 引用有效性 / 引擎接线

覆盖 2026-08-30 Phase 3 验收项:
  分离:     检索 20 条命中, 回答实际用 3 条 → used_count=3, 面板 citations 只含 3 条
  绑定:     TEXTUAL_INFERENCE 允许多条 evidence; SPECULATION 不绑定 DIRECT evidence
  有效性:   引用必须 used_evidence; 仅"检索过"不进面板; 未检索到书单列 unverified
  回归:     general / nietzsche 引用均可见; 跨作者引用不被作者门控过滤;
            /api/cite 点击解析真实章节; done 事件带 evidence 契约
"""
import os
import sys
import asyncio
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import AIMessageChunk, ToolMessage

import evidence_contract as ec
from routes import agent as AG

BASE = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


# ═══════════════════════════════════════════════════════
# 辅助: 检索命中 / tool_log 构建
# ═══════════════════════════════════════════════════════
def _hit(book, chapter, author="加缪", book_id="book_x", idx=0, score=0.9,
         snippet="加缪在第1段写道: 荒诞在于把意义强加给世界。"):
    return {"book_id": book_id, "book_title": book, "author": author,
            "chapter_idx": idx, "chapter_title": chapter,
            "snippet": snippet, "score": score}


def _search_tool(results):
    return {"name": "search_books", "args": {"query": "test"}, "result_summary": "",
            "result_full": {"results": results, "query": "test"}}


def _contract(results, answer, agent="general", extra_tools=None):
    tl = [_search_tool(results)] + (extra_tools or [])
    return ec.build_evidence_contract(tl, answer, agent)


# ═══════════════════════════════════════════════════════
# 1. retrieved / used 分离（核心验收: 检索 20 用 3 面板 3）
# ═══════════════════════════════════════════════════════
def test_retrieved_20_used_3_panel_shows_3():
    hits = [_hit("西西弗斯神话", "开篇" if i == 0 else f"第{i}节", book_id=f"book_{i}", idx=i,
                 score=round(1.0 - i * 0.01, 3),
                 snippet=f"加缪在第{i + 1}段写道: 荒诞在于把意义强加给世界。") for i in range(20)]
    answer = ("荒诞是加缪的核心命题【《西西弗斯神话》·开篇】；他把它推进到第2节【《西西弗斯神话》·第2节】，"
              "并在第3节给出了回答【《西西弗斯神话》·第3节】。")
    c = _contract(hits, answer)
    assert c["retrieved_count"] == 20
    assert c["used_count"] == 3, "检索 20 条, 回答实际用 3 条"
    assert len(c["used_evidence"]) == 3
    assert len(c["citations"]) == 3, "引用面板只展示 used_evidence"
    assert sum(1 for ev in c["retrieved_evidence"] if ev["used"]) == 3
    assert all(ci["used"] is True for ci in c["citations"])
    assert all(ci["evidence_id"] for ci in c["citations"])
    # 未用候选不得进面板: 逐条核对书/章节 属于用到的 3 条
    used_keys = {(ci["book_id"], ci["chapter_idx"]) for ci in c["citations"]}
    for ev in c["retrieved_evidence"]:
        assert (ev["book_id"], ev["chapter_idx"]) in used_keys or ev["used"] is False


def test_search_books_author_gate_removed_for_non_general():
    """非 general 智能体不再按作者过滤证据——跨作者引用（如尼采引加缪）不被抹掉"""
    hits = [_hit("查拉图斯特拉如是说", "前言·4", author="弗里德里希·尼采", book_id="z1", idx=4),
            _hit("西西弗斯神话", "开篇", author="加缪", book_id="s1", idx=0)]
    answer = ("如我所说【《查拉图斯特拉如是说》·前言·4】；加缪的荒诞是另一种图景【《西西弗斯神话》·开篇】。")
    c = _contract(hits, answer, agent="nietzsche")
    books = {ci["book"] for ci in c["citations"]}
    assert "查拉图斯特拉如是说" in books and "西西弗斯神话" in books, "跨作者引用不得被门控过滤"
    assert c["used_count"] == 2


# ═══════════════════════════════════════════════════════
# 2. Claim → Evidence 绑定
# ═══════════════════════════════════════════════════════
def test_textual_inference_binds_multiple_evidence():
    hits = [_hit("西西弗斯神话", "开篇", book_id="b1", idx=0, snippet="荒诞在于把意义强加给世界。"),
            _hit("西西弗斯神话", "第2节", book_id="b2", idx=1, snippet="对荒诞的反抗是自由的开始。")]
    answer = "这意味着荒诞的自由【《西西弗斯神话》·开篇】，并延续到第2节【《西西弗斯神话》·第2节】。"
    c = _contract(hits, answer)
    claim = c["claims"][0]
    assert claim["epistemic_type"] == "TEXTUAL_INFERENCE"
    assert len(claim["evidence_ids"]) == 2, "TEXTUAL_INFERENCE 允许多条 evidence"
    assert claim["direct_evidence"] is True
    # 反向绑定: 两条证据的 supports_claim_ids 都指向该 claim
    for eid in claim["evidence_ids"]:
        ev = next(e for e in c["retrieved_evidence"] if e["evidence_id"] == eid)
        assert claim["claim_id"] in ev["supports_claim_ids"]


def test_speculation_claim_never_binds_direct_evidence():
    hit = _hit("西西弗斯神话", "荒诞的自由", book_id="s1", idx=0,
               snippet="一种荒诞的自由, 西西弗斯推石上山。")
    answer = "一种可能的解释是, 荒诞的自由在于西西弗斯对命运的反抗【《西西弗斯神话》·荒诞的自由】。"
    c = _contract([hit], answer)
    assert c["used_count"] == 1   # 正文引用了该出处（面板可展示）
    claim = c["claims"][0]
    assert claim["epistemic_type"] == "SPECULATION"
    assert claim["evidence_ids"] == [], "SPECULATION 不得伪装拥有 DIRECT evidence"
    assert claim["direct_evidence"] is False
    for ev in c["retrieved_evidence"]:
        assert claim["claim_id"] not in ev["supports_claim_ids"], "推测 claim 不得挂到任何证据上"


def test_snippet_overlap_marks_used_without_citation_marker():
    hits = [_hit("西西弗斯神话", "开篇", book_id="s1", idx=0,
                 snippet="荒诞在于把意义强加给世界, 而当人不再改变世界。", score=0.5)]
    answer = "他写道: 荒诞在于把意义强加给世界。"   # 无引用标注, 但摘引了检索片段
    c = _contract(hits, answer)
    assert c["used_count"] == 1
    assert c["citations"][0]["book"] == "西西弗斯神话"


# ═══════════════════════════════════════════════════════
# 3. Citation Validity
# ═══════════════════════════════════════════════════════
def test_unverified_citation_excluded_from_panel():
    hits = [_hit("西西弗斯神话", "开篇", book_id="b1", idx=0)]
    answer = "荒诞是加缪的命题【《西西弗斯神话》·开篇】；而另一个世界是柏拉图的地图【《理想国》·卷十】。"
    c = _contract(hits, answer)
    unv = c["unverified_citations"]
    assert any(u["book"] == "理想国" and u["reason"] == "book_not_retrieved" for u in unv)
    assert all(ci["book"] != "理想国" for ci in c["citations"]), "仅检索过/未核验引用不得进面板"
    assert c["used_count"] == 1
    assert c["citations"][0]["book"] == "西西弗斯神话"


def test_same_chapter_deduplicated():
    tl = [_search_tool([_hit("西西弗斯神话", "开篇", book_id="b1", idx=0),
                        _hit("西西弗斯神话", "开篇", book_id="b1", idx=0)])]
    c = ec.build_evidence_contract(tl, "")
    assert c["retrieved_count"] == 1, "同一章节重复命中合并为一条证据"


def test_websearch_secondary_never_in_citations():
    tl = [_search_tool([]),
          {"name": "websearch", "args": {"query": "x"}, "result_summary": "",
           "result_full": {"url": "https://ex.org", "content": "外网检索内容"}}]
    c = ec.build_evidence_contract(tl, "无原典引用的回答。")
    assert c["retrieved_count"] == 1
    assert c["retrieved_evidence"][0]["source_type"] == "secondary"
    assert c["citations"] == [], "secondary（外网）检索不得进入原典引用面板"


# ═══════════════════════════════════════════════════════
# 4. 引擎接线（mock APP: 工具轮 + 最终回答; 不调 LLM）
# ═══════════════════════════════════════════════════════
class _FakeToolApp:
    """替换 LangGraph APP.astream: 宣告工具 → 工具结果 → 最终回答 三轮回"""

    def __init__(self, tool_name, tool_args, tool_result, answer):
        self.tool_name, self.tool_args, self.tool_result, self.answer = \
            tool_name, tool_args, tool_result, answer
        self.captured_messages = []

    async def astream(self, inputs, config, stream_mode="messages"):
        self.captured_messages.extend(inputs.get("messages") or [])
        yield (AIMessageChunk(content="", tool_call_chunks=[
            {"name": self.tool_name, "args": "", "id": "call_1", "index": 0}]),
            {"langgraph_node": "agent"})
        yield (ToolMessage(content=json.dumps(self.tool_result, ensure_ascii=False),
                           name=self.tool_name, tool_call_id="call_1",
                           additional_kwargs={"_args": self.tool_args,
                                              "_result_full": self.tool_result}),
               {"langgraph_node": "tools"})
        yield AIMessageChunk(content=self.answer), {"langgraph_node": "agent"}


async def _run_stream(monkeypatch, question, tool_result, answer, agent="general"):
    import engine_langgraph as elg
    fake = _FakeToolApp("search_books", {"query": "test"}, tool_result, answer)
    monkeypatch.setattr(elg, "APP", fake)
    # 后处理两个 LLM 调用用空应答 stub——绝不触达真实 API
    monkeypatch.setattr(AG, "llm_chat",
                        lambda *a, **k: {"choices": [{"message": {"content": ""}}]})
    evs = [ev async for ev in elg.stream_agent(question, [], agent, None, "zh")]
    return evs, fake


def test_stream_agent_general_evidence_contract(monkeypatch):
    hits = [_hit("西西弗斯神话", "开篇", author="加缪", book_id="b1", idx=0)]
    answer = "荒诞是加缪的核心命题【《西西弗斯神话》·开篇】。"
    evs, fake = asyncio.run(_run_stream(monkeypatch, "什么是荒诞的自由", {"results": hits, "query": "荒诞"},
                                        answer, "general"))
    done = next(ev for ev in evs if ev["type"] == "done")
    assert done["type"] == "done"
    assert done["citations"], "general 引用面板不得为空"
    assert done["citations"][0]["book"] == "西西弗斯神话"
    assert done["citations"][0]["used"] is True
    ev = done["evidence"]
    assert ev["retrieved_count"] == 1 and ev["used_count"] == 1
    assert ev["used_evidence"][0]["evidence_id"] == done["citations"][0]["evidence_id"]
    assert any(c["epistemic_type"] in ("SOURCE_FACT",) for c in ev["claims"])


def test_stream_agent_nietzsche_citations_not_hidden(monkeypatch):
    """非 general 智能体的引用必须可见（旧 bug: agent !== 'general' → citation 隐藏）"""
    hits = [_hit("查拉图斯特拉如是说", "前言·4", author="弗里德里希·尼采", book_id="z1", idx=4,
                 snippet="人是应当被超越的——你们已经超越过的, 要我传的是什么?" )]
    answer = "我在《查拉图斯特拉如是说》·前言·4里说过, 人是应当被超越的【《查拉图斯特拉如是说》·前言·4】。"
    evs, fake = asyncio.run(_run_stream(monkeypatch, "你怎么看待孤独", {"results": hits, "query": "孤独"},
                                        answer, "nietzsche"))
    done = next(ev for ev in evs if ev["type"] == "done")
    assert done["citations"], "nietzsche 智能体引用不得隐藏"
    assert done["citations"][0]["book"] == "查拉图斯特拉如是说"
    assert done["citations"][0]["used"] is True


def test_stream_agent_cross_author_citation_kept(monkeypatch):
    hits = [_hit("查拉图斯特拉如是说", "前言·4", author="弗里德里希·尼采", book_id="z1", idx=4),
            _hit("西西弗斯神话", "开篇", author="加缪", book_id="s1", idx=0)]
    result = {"results": hits, "query": "对比"}
    answer = ("我在自己的书里说过人应当被超越【《查拉图斯特拉如是说》·前言·4】；"
              "加缪的荒诞则是另一幅图景【《西西弗斯神话》·开篇】。")
    evs, fake = asyncio.run(_run_stream(monkeypatch, "与我对比一下加缪", result, answer, "nietzsche"))
    done = next(ev for ev in evs if ev["type"] == "done")
    books = {c["book"] for c in done["citations"]}
    assert "查拉图斯特拉如是说" in books and "西西弗斯神话" in books, "跨作者引用不得被作者门控过滤"
    assert done["evidence"]["used_count"] == 2


# ═══════════════════════════════════════════════════════
# 5. 引用点击正确性: /api/cite 解析真实书籍章节（与前端点击同一端点）
# ═══════════════════════════════════════════════════════
def test_api_cite_click_resolves_real_book():
    from fastapi.testclient import TestClient
    try:
        from routes.agent import chapter_meta
    except Exception:
        chapter_meta = None
    books = json.load(open(os.path.join(BASE, "..", "app", "public", "books.json"), encoding="utf-8"))
    chapters_dir = os.path.join(BASE, "data", "book_chapters")
    pick = next((b for b in books
                 if b.get("id") and os.path.isdir(os.path.join(chapters_dir, b["id"]))), None)
    assert pick, "库中应存在可读章节的书, 供点击测试定位"
    meta = chapter_meta(pick["id"]) if chapter_meta else None
    toc = (meta.get("toc") or []) if meta else []
    first = next((t for t in toc if not (isinstance(t, dict) and t.get("type") == "part")), None)
    assert first is not None, "该书应有可索引章节"
    title = first.get("title") if isinstance(first, dict) else first

    from main import app
    client = TestClient(app)
    resp = client.get("/api/cite", params={"book": pick["title"], "chapter": title})
    d = resp.json()
    assert resp.status_code == 200, resp.text
    assert not d.get("error"), d
    assert d["matched"] is True, "引用点击应精确匹配章节"
    assert d["book_id"] == pick["id"]
    assert d.get("text"), "引用点击应能拿到章节正文片段（阅读器跳转内容）"
