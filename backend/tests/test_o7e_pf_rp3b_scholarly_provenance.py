# -*- coding: utf-8 -*-
"""O7-E PF-RP3B Scholarly Evidence Provenance Integration: S1-S15 回归。

锁死（Reviewer 2026-09-09 PF-RP3B 任务书）:
  S1/S2  search_scholarship / get_scholarly_source 执行 → 进入 raw_tool_log
  S3     scholarly metadata → scholarly_records
  S4     METADATA_ONLY 记录不得成为内容证据
  S5     返回 abstract → ABSTRACT_AVAILABLE 证据
  S6     FULL_TEXT_AVAILABLE 未读 → 无内容证据
  S7     FULL_TEXT_READ + passages → 内容证据
  S8     scholarly 记录永不进入原典引用面板
  S9-S11 judge 收到 SECONDARY_SOURCE_RECORDS / ACCESS_LEVELS / 二手证据文本
  S12    post-hoc registry lookup = 0
  S13/S14 精确脚本化 Strawson 记录 / Boeker 摘要端到端存活
  S15    缺失的 scholarly 记录保持缺失（无机械"现实救援"）
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine_langgraph as EG
import evidence_contract as EC
import routes.agent as AG

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_o2_final_ownership import (_msg, _done, _TOOLS_SCRIPT, ScriptedChat,
                                     _fake_tools, _STUB_CALLS)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools", "evaluation"))
import o7e_bakeoff_judge2 as J2
from o7e_production_calibration import run_case_production

# ═══════════════════════════════════════════════════════
# fake scholarly tools（形状复刻 O7-C 真实输出）
# ═══════════════════════════════════════════════════════
_STRAWSON_SEARCH = {
    "query": "locke personal identity",
    "results": [{"source_record_id": "o7d_test:strawson-2017",
                 "title": "Locke on Personal Identity",
                 "authors": [{"name": "Galen Strawson"}],
                 "year": 2017, "publication_type": "book-chapter",
                 "venue": "Princeton University Press", "doi": None,
                 "access_level": "ABSTRACT_AVAILABLE",
                 "provider": "LOCAL_CURATED"}],
    "providers_queried": ["LOCAL_CURATED"]}

_STRAWSON_ABSTRACT = ("Strawson argues that the person is a forensic term and that "
                      "praise and blame, punishment and reward attach to consciousness; "
                      "he defends a hybrid interpretation of Locke on personal identity.")

_STRAWSON_GET = {
    "source_record_id": "o7d_test:strawson-2017",
    "bibliographic_record": {"source_record_id": "o7d_test:strawson-2017",
                             "title": "Locke on Personal Identity"},
    "access_level_before": "ABSTRACT_AVAILABLE",
    "access_level_after": "ABSTRACT_AVAILABLE",
    "returned_evidence_level": "ABSTRACT_AVAILABLE",
    "full_text_status": "NOT_OPEN",
    "content_hash": "deadbeef",
    "abstract": {"text": _STRAWSON_ABSTRACT, "source": "crossref", "hash": "x"},
}

_BOEKER_GET = {
    "source_record_id": "o7d_test:boeker-2021",
    "bibliographic_record": {"source_record_id": "o7d_test:boeker-2021",
                             "title": "Personal Identity, Transitivity, and Divine Justice"},
    "access_level_before": "METADATA_ONLY",
    "access_level_after": "ABSTRACT_AVAILABLE",
    "returned_evidence_level": "ABSTRACT_AVAILABLE",
    "full_text_status": "NOT_OPEN",
    "content_hash": "feedface",
    "abstract": {"text": "Boeker discusses the transitivity problem, the afterlife and "
                         "the last judgement, and a hybrid interpretation of Locke.",
                 "source": "crossref", "hash": "y"},
}


def _scholarly_tools(extra=None):
    from langchain_core.tools import StructuredTool

    def _get(source_record_id: str = "", requested_access: str = "ABSTRACT"):
        if "boeker" in source_record_id:
            return dict(_BOEKER_GET)
        return dict(_STRAWSON_GET)

    tools = _fake_tools()
    tools.append(StructuredTool.from_function(
        func=lambda **a: dict(_STRAWSON_SEARCH), name="search_scholarship",
        description="search_scholarship stub"))
    tools.append(StructuredTool.from_function(
        func=_get, name="get_scholarly_source",
        description="get_scholarly_source stub"))
    for t in (extra or []):
        tools.append(t)
    return tools


def _run(question, script, agent="general"):
    for k in _STUB_CALLS:
        _STUB_CALLS[k] = []
    orig = (EG.get_llm, EG.get_tools, AG.llm_chat)
    chat = ScriptedChat(script=list(script))
    EG.get_llm = lambda: chat
    EG.get_tools = lambda a: _scholarly_tools()
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


_GOOD = "孔子评价鲁人改建长府时说闵子骞不苟言笑、说话必定切中要点，判断人应听其言而观其行。"

_S1_SCRIPT = _TOOLS_SCRIPT + [
    _msg("查一下 Locke 个人同一性的学术文献。",
         [{"name": "search_scholarship",
           "args": {"query": "locke personal identity"}, "id": "s1"}]),
    _msg("读 Strawson 2017 的摘要。",
         [{"name": "get_scholarly_source",
           "args": {"source_record_id": "o7d_test:strawson-2017",
                    "requested_access": "ABSTRACT"}, "id": "s2"}]),
    _msg(_GOOD),
]


def _scholarly_sources(evs):
    done = next(e for e in reversed(evs) if e.get("type") == "done")
    return done.get("scholarly_sources") or {}


# ── S1/S2/S3/S13: 端到端执行 → raw log → provenance ──
def test_s1_s2_s13_scholarly_calls_captured_end_to_end():
    evs = _run("言必有中出处", _S1_SCRIPT)
    ss = _scholarly_sources(evs)
    assert ss.get("scholarly_search_calls") == 1            # S1
    assert ss.get("scholarly_source_fetch_calls") == 1      # S2
    recs = ss.get("scholarly_records") or []
    assert recs and recs[0]["source_record_id"] == "o7d_test:strawson-2017"
    assert recs[0]["publication_year"] == 2017
    evs_ids = [e.get("source_record_id") for e in ss.get("scholarly_evidence") or []]
    assert "o7d_test:strawson-2017" in evs_ids              # S13: 端到端存活


def test_s14_scripted_boeker_abstract_survives():
    script = _TOOLS_SCRIPT + [
        _msg("再读 Boeker 2021。",
             [{"name": "get_scholarly_source",
               "args": {"source_record_id": "o7d_test:boeker-2021",
                        "requested_access": "ABSTRACT"}, "id": "s14"}]),
        _msg(_GOOD)]
    evs = _run("言必有中出处", script)
    ss = _scholarly_sources(evs)
    ev_entries = ss.get("scholarly_evidence") or []
    assert any("transitivity" in (e.get("abstract_text") or "")
               for e in ev_entries)                         # Boeker 摘要端到端存活


# ── S3-S7: build_scholarly_provenance 语义（access 态机零偏离）──
def _prov(log):
    return EC.build_scholarly_provenance(log)


def test_s3_metadata_records_to_records():
    log = [{"name": "search_scholarship", "result_full": _STRAWSON_SEARCH}]
    p = _prov(log)
    assert len(p["scholarly_records"]) == 1
    assert p["scholarly_records"][0]["title"] == "Locke on Personal Identity"
    assert p["scholarly_facts"]["record_count"] == 1


def test_s4_metadata_only_never_content_evidence():
    log = [{"name": "get_scholarly_source", "result_full": {
        "source_record_id": "r1", "access_level_before": "METADATA_ONLY",
        "access_level_after": "METADATA_ONLY",
        "returned_evidence_level": "METADATA_ONLY"}}]
    p = _prov(log)
    assert p["scholarly_evidence"][0]["abstract_text"] == ""
    assert p["scholarly_evidence"][0]["evidence_passages"] == []
    assert p["scholarly_access"]["r1"] == "METADATA_ONLY"


def test_s5_abstract_becomes_abstract_evidence():
    log = [{"name": "get_scholarly_source", "result_full": dict(_STRAWSON_GET)}]
    p = _prov(log)
    assert _STRAWSON_ABSTRACT in p["scholarly_evidence"][0]["abstract_text"]
    assert p["scholarly_access"]["o7d_test:strawson-2017"] == "ABSTRACT_AVAILABLE"


def test_s6_full_text_available_without_read_no_content():
    log = [{"name": "get_scholarly_source", "result_full": {
        "source_record_id": "r2", "access_level_before": "METADATA_ONLY",
        "access_level_after": "FULL_TEXT_AVAILABLE",
        "returned_evidence_level": "FULL_TEXT_AVAILABLE",
        "full_text_status": "OPEN_AVAILABLE_NO_READ"}}]
    p = _prov(log)
    assert p["scholarly_evidence"][0]["abstract_text"] == ""
    assert p["scholarly_evidence"][0]["evidence_passages"] == []


def test_s7_full_text_read_passages_are_content_evidence():
    log = [{"name": "get_scholarly_source", "result_full": {
        "source_record_id": "r3", "access_level_before": "FULL_TEXT_AVAILABLE",
        "access_level_after": "FULL_TEXT_READ",
        "returned_evidence_level": "FULL_TEXT_READ",
        "evidence_passages": [{"text": "passage 一"}, {"text": "passage 二"}]}}]
    p = _prov(log)
    assert p["scholarly_evidence"][0]["evidence_passages"] == ["passage 一", "passage 二"]


def test_s8_scholarly_never_enters_primary_citation_panel():
    # scholarly 原始条目不进入 evidence pool（→ 永不进 used_evidence/citations）
    log = [{"name": "search_scholarship", "result_full": _STRAWSON_SEARCH},
           {"name": "get_scholarly_source", "result_full": dict(_STRAWSON_GET)}]
    pool = EC.build_evidence_pool(log)
    assert all(e.get("kind") not in ("scholarly",) for e in pool)
    contract = EC.build_evidence_contract(log, "正文。", "general", "zh")
    assert all("strawson" not in json.dumps(u, ensure_ascii=False).lower()
               for u in contract.get("used_evidence") or [])
    assert contract.get("scholarly_records")                   # 但 provenance 独立在


# ── S9-S11: judge 收到三类正式字段 ──
def _record_with_scholarly():
    return {"case_id": "sx", "answer": "Strawson (2017) 讨论洛克的人格同一性。",
            "citations": [], "quote_bound": [],
            "evidence_digest": {"facts": {"read_chapters": []},
                                 "used_evidence": []},
            "scholarly_provenance": {
                "SCHOLARLY_SEARCH_CALLS": 1,
                "SCHOLARLY_SOURCE_FETCH_CALLS": 1,
                "SCHOLARLY_RECORD_IDS": ["o7d_test:strawson-2017"],
                "SCHOLARLY_EVIDENCE_RECORD_IDS": ["o7d_test:strawson-2017"],
                "SCHOLARLY_ACCESS_LEVELS": {"o7d_test:strawson-2017":
                                            "ABSTRACT_AVAILABLE"},
                "scholarly_records": [{"source_record_id": "o7d_test:strawson-2017",
                                       "title": "Locke on Personal Identity",
                                       "authors": ["Galen Strawson"],
                                       "publication_year": 2017}],
                "scholarly_evidence": [{"source_record_id": "o7d_test:strawson-2017",
                                        "abstract_text": _STRAWSON_ABSTRACT,
                                        "access_level_after": "ABSTRACT_AVAILABLE",
                                        "evidence_passages": []}],
            }}


def test_s9_s10_s11_judge_receives_runtime_scholarly_evidence():
    r = _record_with_scholarly()
    primary_ev, secondary, access_levels = J2._judge_evidence_parts(r)
    sec_strawson = [s for s in secondary
                    if s.get("source_record_id") == "o7d_test:strawson-2017"]
    assert sec_strawson, "S9: judge 必须收到 SECONDARY_SOURCE_RECORDS"
    assert sec_strawson[0].get("abstract_text")                # S11: 实际二手证据文本
    assert access_levels and access_levels[0]["access_level"] == "ABSTRACT_AVAILABLE"  # S10


def test_s12_posthoc_registry_lookup_zero():
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "tools", "evaluation",
        "o7e_bakeoff_judge2.py"), encoding="utf-8").read()
    assert "scholarly_sources" not in src.replace(
        "scholarly_source_fetch_calls", "").replace(
        "get_scholarly_source", "") or "import scholarly_sources" not in src
    assert "import scholarly_sources" not in src and "SS." not in src


def test_s15_missing_record_stays_missing():
    # 无 scholarly provenance 的 run → judge secondary 无记录（无机械现实救援）
    r = {"case_id": "s15", "answer": "Strawson (2017) 讨论洛克。",
         "citations": [], "quote_bound": [],
         "evidence_digest": {"facts": {"read_chapters": []}, "used_evidence": []},
         "scholarly_provenance": {"SCHOLARLY_SEARCH_CALLS": 0,
                                  "SCHOLARLY_SOURCE_FETCH_CALLS": 0,
                                  "SCHOLARLY_RECORD_IDS": [],
                                  "SCHOLARLY_EVIDENCE_RECORD_IDS": [],
                                  "SCHOLARLY_ACCESS_LEVELS": {},
                                  "scholarly_records": [], "scholarly_evidence": []}}
    _primary, secondary, access = J2._judge_evidence_parts(r)
    assert not [s for s in secondary if s.get("source_record_id")]
    assert access == []
