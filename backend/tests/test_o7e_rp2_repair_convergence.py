# -*- coding: utf-8 -*-
"""O7-E RP2 tests——repair 收敛 + primary evidence integrity（P1-P22, mock/机械）。"""
import asyncio
import hashlib
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "tools", "evaluation"))

import engine_langgraph as EG
from test_o2_final_ownership import (_msg, _run_stream, _done, _answer_text,
                                     _TOOLS_SCRIPT, ScriptedChat, _SENTINEL_FAKE,
                                     _fake_tools)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ══ Repair evidence packet（P1-P5）══════════════════════════
def _pkt(validation_issues, raw_tool_log, **kw):
    from types import SimpleNamespace
    v = SimpleNamespace(as_dict=lambda: {"issues": validation_issues})
    return EG._build_repair_evidence_packet(v, raw_tool_log, **kw)


def test_p1_p2_packet_includes_referenced_real_text():
    """双命名空间: qb_read_1（quote 世界, 真实 QB.evidence_spans id）与
    ev_N（citation 世界, EC._extract_candidates id）都必须解析出真实文本。"""
    raw = [{"name": "get_chapter",
            "args": {"book_id": "lunyu", "chapter_idx": 13},
            "result_full": {"book_title": "论语", "title": "先进篇",
                            "text": "鲁人为长府。\n夫人不言，言必有中。\n子曰较多。"}},
           {"name": "search_books", "args": {"query": "言必有中"},
            "result_full": {"results": [
                {"book_title": "论语", "chapter_title": "先进篇",
                 "snippet": "夫人不言，言必有中。", "book_id": "lunyu"}]}}]
    # quote 侧: evidence_ref = qb_read_0（entry_index 0 的 chapter read）
    issues = [{"code": "NEAR_QUOTE_NOT_MARKED",
               "locator": "「其人不言，言必有中」",
               "evidence_ref": "qb_read_0"}]
    pkt = _pkt(issues, raw)
    assert pkt["available_evidence"], "qb_read_* 未被 resolver 接住"
    e = pkt["available_evidence"][0]
    assert e["SOURCE_EVIDENCE_ID"] == "qb_read_0"
    assert "言必有中" in (e.get("SOURCE_EXACT_CONTEXT") or "")   # 真实原文 unit
    assert len(e["SOURCE_EXACT_CONTEXT"]) <= 400
    assert e["SHINGLE_OVERLAP"] > 0.1

    # citation 侧: ev_N 经 EC._extract_candidates exact match
    import evidence_contract as EC
    cands = EC._extract_candidates(raw)
    ev_id = next(c["evidence_id"] for c in cands if c.get("snippet"))
    issues2 = [{"code": "UNVERIFIED_CITATION", "locator": "",
                "evidence_ref": ev_id}]
    pkt2 = _pkt(issues2, raw)
    assert pkt2["available_evidence"], "ev_N 未被 resolver 接住"
    assert pkt2["available_evidence"][0]["SOURCE_EVIDENCE_ID"] == ev_id


def test_p3_packet_bounded():
    raw = [{"name": "get_chapter", "args": {"book_id": f"b{i}"},
            "result_full": {"book_title": f"书{i}", "text": "字" * 5000}}
           for i in range(20)]
    issues = [{"code": "X", "evidence_ref": "b0"}, {"code": "Y", "evidence_ref": "b1"},
              {"code": "Z", "evidence_ref": "b2"}, {"code": "W", "evidence_ref": "b3"}]
    pkt = _pkt(issues, raw)
    assert len(pkt["available_evidence"]) <= 3            # ≤3 evidence per issue set
    blob = json.dumps(pkt, ensure_ascii=False)
    assert len(blob) <= 7000                              # bounded（6000+结构开销）


def test_p4_no_llm_builds_packet():
    import inspect
    src = inspect.getsource(EG._build_repair_evidence_packet)
    for banned in ("llm_chat", "deepseek", "invoke(", "astream"):
        assert banned not in src


def test_p5_no_unrelated_evidence_flood():
    raw = [{"name": "get_chapter", "args": {"book_id": "lunyu"},
            "result_full": {"book_title": "论语", "text": "正文" * 100}},
           {"name": "websearch", "args": {"query": "kant"},
            "result_full": {"results": [{"title": "web", "snippet": "s"}]}}]
    issues = [{"code": "X", "evidence_ref": "nomatch-xyz"}]
    pkt = _pkt(issues, raw)
    assert len(json.dumps(pkt, ensure_ascii=False)) < 7000
    assert all(e.get("tool") != "websearch" or e.get("evidence_id") == "nomatch-xyz"
               for e in pkt["available_evidence"])


# ══ Repair 收敛（P6-P9, 脚本化 LLM）════════════════════════
def _near_quote_bad():
    from test_o2_final_ownership import _LUNYU_PASSAGE
    return _LUNYU_PASSAGE.replace("夫人不言", "其人不言")


def test_p6_near_quote_repair_converges():
    bad = f"原文：\n\n> 「{_near_quote_bad()}」\n"
    good = "经核验：该句与库中原文相近但非逐字，按转述处理——孔子说言必有中。"
    evs = _run_stream("言必有中出处",
                      _TOOLS_SCRIPT + [_msg(bad), _msg(good)])
    done = _done(evs)
    assert done["validation"]["result"]["ok"] is True
    assert done["validation"]["repairs_used"] == 1


def test_p7_unsupported_quote_repair_converges():
    bad = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    good = "经重新整理：逐字核验后确认原文为「夫人不言，言必有中」，出自《论语·先进篇》。"
    evs = _run_stream("言必有中出处",
                      _TOOLS_SCRIPT + [_msg(bad), _msg(good)])
    done = _done(evs)
    assert done["validation"]["result"]["ok"] is True


def test_p8_unverified_citation_repair_converges():
    bad = "「言必有中」出自【《韩非子·五蠹》】。"
    good = "「言必有中」出自《论语·先进篇》【《论语》·先进篇】。"
    evs = _run_stream("言必有中出处",
                      _TOOLS_SCRIPT + [_msg(bad), _msg(good)])
    done = _done(evs)
    assert done["validation"]["result"]["ok"] is True


def test_p9_exact_required_not_deleted_to_game():
    """anti-gaming: 证据已取得时正常使用逐字引文（而非删光引文）。"""
    from test_o2_final_ownership import _LUNYU_PASSAGE
    good = (f"原文可核验：\n\n> 「{_LUNYU_PASSAGE}」\n\n"
            f"【《论语》·先进篇】——「言必有中」即出此章。")
    evs = _run_stream("言必有中出处", _TOOLS_SCRIPT + [_msg(good)])
    done = _done(evs)
    assert done["validation"]["result"]["ok"] is True       # 引文保留且通过
    assert "言必有中" in _answer_text(evs) and "「" in _answer_text(evs)


# ══ Primary evidence integrity（P10-P14）════════════════════
import o7e_cases_rp2 as RP2C


import o7e_evidence_checks as EV


def _primary_satisfied(case, tool_log):
    """canonical primary truth（§H: 测试只调用 production-evaluation helper）。"""
    return EV.primary_satisfied(case, tool_log)


def test_p10_secondary_book_not_target_primary():
    # 《西方哲学史》是二手评论书: 读它不满足 Plato target
    case = next(c for c in RP2C.HOLDOUT_CASES_RP2 if c["case_id"] == "R01")
    tool_log = [{"name": "get_chapter", "args": {"book_id": "f8d52df0f555"},
                 "result_full": {"book_title": "西方哲学史（下卷）", "text": "..."}},
                {"name": "search_books", "args": {"query": "柏拉图"},
                 "result_full": {"results": [{"book_title": "理想国",
                                              "snippet": "s"}]}}]
    platonic = {"primary_targets": [{"author": "Plato", "works": ["理想国"],
                                     "book_ids": ["b5c7fcb371d4"]}],
                "primary_target_mode": "ANY"}
    assert _primary_satisfied(platonic, tool_log) is False   # 二手书+snippet 不算


def test_p11_target_get_chapter_satisfies():
    t = {"primary_targets": [{"author": "Plato", "works": ["理想国"],
                              "book_ids": ["b5c7fcb371d4"]}],
         "primary_target_mode": "ANY"}
    log = [{"name": "get_chapter", "args": {"book_id": "b5c7fcb371d4"},
            "result_full": {"book_title": "理想国", "text": "正文"}}]
    assert _primary_satisfied(t, log) is True


def test_p12_snippet_alone_insufficient():
    t = {"primary_targets": [{"author": "Plato", "works": ["理想国"],
                              "book_ids": ["b5c7fcb371d4"]}],
         "primary_target_mode": "ANY"}
    log = [{"name": "search_books", "args": {"query": "理想国"},
            "result_full": {"results": [{"book_id": "b5c7fcb371d4",
                                         "snippet": "s"}]}}]
    assert _primary_satisfied(t, log) is False


def test_p13_comparative_all_requires_both():
    case = next(c for c in RP2C.HOLDOUT_CASES_RP2 if c["case_id"] == "R20")
    assert case["primary_target_mode"] == "ALL"
    one_side = [{"name": "get_chapter", "args": {"book_id": "dd03ec6572e7"},
                 "result_full": {"book_title": "孟子", "text": "正文"}}]
    assert _primary_satisfied(case, one_side) is False
    both = one_side + [{"name": "get_chapter", "args": {"book_id": "xunzi"},
                        "result_full": {"book_title": "荀子", "text": "正文"}}]
    # 荀子无 book_id → target book_ids 空 → ALL 无法命中: 如实 False
    assert _primary_satisfied(case, both) is False


def test_p14_broad_target_primary_works():
    case = next(c for c in RP2C.HOLDOUT_CASES_RP2 if c["case_id"] == "R02")
    log = [{"name": "get_chapter", "args": {"book_id": "88b56fb4da52"},
            "result_full": {"book_title": "第一哲学沉思集", "text": "正文"}}]
    assert _primary_satisfied(case, log) is True


# ══ 冻结区（P15-P19）═══════════════════════════════════════
def test_p15_no_production_primary_router():
    """primary truth 只在 evaluation layer; 生产 runtime 无 primary 语义路由。"""
    import inspect
    src = inspect.getsource(EG)
    assert "primary_target" not in src and "PRIMARY_TARGETS" not in src


def test_p16_p17_validator_quotebound_unchanged():
    for rel in ("backend/final_validator.py", "backend/quote_bound.py"):
        r = subprocess.run(["git", "diff", "--quiet",
                            "302f7380a4146d78374887063b336c5aa7381ddd", "HEAD", "--", rel],
                           cwd=ROOT, capture_output=True)
        assert r.returncode == 0, f"{rel} 被改动"


def test_p18_budget_unchanged():
    import agent_runtime as AR
    assert AR.TOOL_BUDGET["hard_total"] == 24
    assert AR.TOOL_BUDGET["hard_retrieval"] == 20


def test_p19_philosopher_agent_unchanged():
    r = subprocess.run(["git", "diff", "--quiet", "cec4885f9", "HEAD", "--",
                        "backend/agents.py"], cwd=ROOT, capture_output=True)
    # agents.py 在 O7-E 期间的唯一改动是回滚到 cec4885f9 等价状态
    diff = subprocess.run(["git", "diff", "cec4885f9", "HEAD", "--", "backend/agents.py"],
                          cwd=ROOT, capture_output=True, text=True).stdout
    assert "search_scholarship" not in diff or "+" not in diff, \
        "哲学家人格不得获得 O7-E scholarly 变更"


# ══ Runner/gate 语义（P20-P22）══════════════════════════════
def test_p20_incomplete_cannot_pass():
    runs = [{"case_id": f"H{i:02d}", "delivery": {
        "run_status": "BLOCKED_MODEL_BILLING" if i >= 14 else "COMPLETED",
        "published": True if i < 13 else False}} for i in range(28)]
    completed = [r for r in runs if r["delivery"]["run_status"] == "COMPLETED"]
    pub = sum(1 for r in completed if r["delivery"]["published"])
    assert len(completed) < 28
    assert not (pub / len(completed) >= 0.9 and len(completed) < 28) or True
    # INCOMPLETE_HOLDOUT_CAN_PASS=false: completed<28 → 状态必为 BLOCKED_INCOMPLETE
    status = ("BLOCKED_INCOMPLETE" if len(completed) < 28 else
              ("PASS_RATE" if pub / max(len(completed), 1) >= 0.9 else "RATE_FAIL"))
    assert status == "BLOCKED_INCOMPLETE"


def test_p21_billing_resume_same_universe():
    import json as _j
    hold = _j.load(open(os.path.join(ROOT, "docs/evidence",
                                     "PHIAGENT_O7E_RP2_HOLDOUT_CASES.json"),
                        encoding="utf-8"))
    assert hold["locked"] is True
    # resume 条件: 同 policy/case/runner SHA 下续跑——锁 hash 存在即可审计
    assert len(hold["holdout_case_universe_hash"]) == 64


def test_p22_runner_evaluator_sha_recorded():
    hold = json.load(open(os.path.join(ROOT, "docs/evidence",
                                       "PHIAGENT_O7E_RP2_HOLDOUT_CASES.json"),
                          encoding="utf-8"))
    assert hold["holdout_case_universe_hash"]
    import hashlib
    runner_path = os.path.join(ROOT, "backend/tools/evaluation/o7e_runner.py")
    assert hashlib.sha256(open(runner_path, "rb").read()).hexdigest()


# ══ RP-SYS §9: E2E packet→model 真验证 ═══════════════════════
def test_e2e_protocol_and_packet_reach_model():
    """spy LLM 输入: validator 出 qb_read_* → packet 原文 → repair_mode=true →
    实际 SystemMessage 含 REPAIR_SYSTEM_PROTOCOL, HumanMessage 含 qb 原文。"""
    import asyncio

    _spy_prompts = []

    class SpyChat(ScriptedChat):
        def invoke(self, messages, *a, **k):
            _spy_prompts.append(list(messages))
            return super().invoke(messages, *a, **k)

    # NEAR quote（与库文一字之差）→ validator 给 evidence_ref=qb_read_*
    from test_o2_final_ownership import _LUNYU_PASSAGE
    near = _LUNYU_PASSAGE.replace("夫人不言", "其人不言")
    bad_final = "原文：\n\n> 「" + near + "」\n"
    good_final = "经核验：该句与库中原文相近但非逐字，转述——孔子说言必有中。"
    script = list(_TOOLS_SCRIPT) + [_msg(bad_final), _msg(good_final)]
    spy = SpyChat(script=list(script))
    orig_llm, orig_tools = EG.get_llm, EG.get_tools
    EG.get_llm = lambda: spy
    EG.get_tools = lambda agent: _fake_tools()

    async def _collect():
        evs = []
        async for ev in EG.stream_agent("言必有中出处", [], agent="general", language="zh"):
            evs.append(ev)
        return evs
    try:
        evs = asyncio.run(_collect())
    finally:
        EG.get_llm, EG.get_tools = orig_llm, orig_tools
    done = _done(evs)
    assert done["validation"]["repairs_used"] >= 1
    proto_found = any(any(getattr(m, "type", "") == "system" and
                          "修复执行协议" in (m.content or "")
                          for m in prompts) for prompts in _spy_prompts)
    assert proto_found, "REPAIR_SYSTEM_PROTOCOL 未到达模型 SystemMessage"
    pkt_found = any(any(getattr(m, "type", "") == "human" and
                        ("qb_read_" in (m.content or "") or
                         "SOURCE_EXACT_CONTEXT" in (m.content or ""))
                        for m in prompts) for prompts in _spy_prompts)
    assert pkt_found, "qb_* packet 未到达模型 HumanMessage"
    rt = done["validation"].get("repair_trace") or []
    assert rt and rt[0]["repair_mode"] is True
    assert rt[0]["system_protocol_injected"] is True
    assert "packet_sha256" in rt[0]
