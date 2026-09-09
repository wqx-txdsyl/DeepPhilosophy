# -*- coding: utf-8 -*-
"""O7-E RCA-1 FINAL DIAGNOSTIC CLOSURE: F1-F12 可执行回归。

Reviewer 2026-09-09 裁决：I5-I8 式源码字符串断言不算 integration test——
本文件全部走 production path（真实 LangGraph 图 + 脚本化假 LLM + 工具桩 +
adapter 注入 stream_agent），锁死：
  F1/F2  unsupported prep → 实际流走 FULL_REWRITE 且 LOCAL_PATCH System 不达模型
  F3-F6  finalization 真实执行：pending 收口 / LOCAL_PATCH System / 零工具 /
         不增 repairs_used / patch 真实 apply
  F7/F8  terminal fingerprint 以 validation.history 为真源 → R1/R2 分类
  F9/F10 trace protocol SHA 按实际 mode 记录（LOCAL≠FULL_REWRITE）
  F11/F12 终态候选非空但无效 ≠ 空候选；未发布 ≠ 终态候选空
"""
import asyncio
import json
import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine_langgraph as EG
import repair_context as RC
import routes.agent as AG
import agent_runtime as AR

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_o2_final_ownership import (_msg, _done, _answer_text, _TOOLS_SCRIPT,
                                     _LUNYU_PASSAGE, _SENTINEL_FAKE,
                                     ScriptedChat, _fake_tools, _STUB_CALLS)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools", "evaluation"))
from o7e_rca1_hook_eval import LocalPatchAdapter, case_result, classify_history

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ENG_SRC = open(os.path.join(_ROOT, "backend", "engine_langgraph.py"),
                encoding="utf-8").read()
_LP_PROTO = _ENG_SRC.split('LOCAL_PATCH_SYSTEM_PROTOCOL = """')[1].split('"""')[0]
_FR_PROTO = _ENG_SRC.split('REPAIR_SYSTEM_PROTOCOL = """')[1].split('"""')[0]


# ═══════════════════════════════════════════════════════
# harness: 录制模型输入的 ScriptedChat + adapter 注入版 stream
# ═══════════════════════════════════════════════════════
class RecordingChat(ScriptedChat):
    seen: list = []          # 每次 LLM invocation 的完整输入消息（role/content）

    def _record(self, messages):
        self.seen.append([{"role": getattr(m, "type", ""),
                           "content": str(getattr(m, "content", ""))}
                          for m in messages])

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        self._record(messages)
        return super()._stream(messages, stop=stop, run_manager=run_manager, **kwargs)

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self._record(messages)
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

    def invoke(self, messages, *a, **k):
        self._record(messages)
        return super().invoke(messages, *a, **k)


def _run_lp(question, script, adapter=None):
    for k in _STUB_CALLS:
        _STUB_CALLS[k] = []
    orig = (EG.get_llm, EG.get_tools, AG.llm_chat)
    chat = RecordingChat(script=list(script))
    EG.get_llm = lambda: chat
    EG.get_tools = lambda agent: _fake_tools()
    AG.llm_chat = lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("收口路径不得调用隐藏 LLM"))

    async def _collect():
        evs = []
        async for ev in EG.stream_agent(question, [], agent="general", language="zh",
                                        _evaluation_repair_adapter=adapter):
            evs.append(ev)
        return evs
    try:
        return asyncio.run(_collect()), chat
    finally:
        EG.get_llm, EG.get_tools, AG.llm_chat = orig


def _trace(evs):
    return _done(evs)["validation"]["repair_trace"]


class _AnchorMissingAdapter(LocalPatchAdapter):
    """模拟自然发生的 UNRESOLVED_ANCHORS（H2C 轮 H13 实况）——全部 quote issue
    的 locator 置为候选中不存在的文本 → prepare 第二条件不过 → supported=False。"""

    def prepare(self, candidate, validation, raw_tool_log, prev_errors=None):
        issues = [dict(i) for i in validation.as_dict().get("issues", [])]
        for i in issues:
            if i.get("code") != "UNVERIFIED_CITATION":
                i["locator"] = "绝不存在于候选中的锚文本定位串"
        v2 = SimpleNamespace(as_dict=lambda iss=issues: {"issues": iss})
        return super().prepare(candidate, v2, raw_tool_log, prev_errors)


_GOOD = "经重新整理：逐字核验后确认，「言必有中」出自孔子对闵子骞的评价。"


# ═══════════════════════════════════════════════════════
# F1/F2: unresolved anchor → 实际流 FULL_REWRITE；LP System 不达模型
# ═══════════════════════════════════════════════════════
def test_f1_unresolved_anchor_stream_uses_full_rewrite():
    bad = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    evs, _chat = _run_lp("言必有中出处", _TOOLS_SCRIPT + [_msg(bad), _msg(_GOOD)],
                         adapter=_AnchorMissingAdapter())
    done = _done(evs)
    trace = _trace(evs)
    assert len(trace) == 1
    assert trace[0]["repair_output_mode"] == "FULL_REWRITE"
    assert trace[0]["lp_gate"]["supported"] is False
    assert "UNRESOLVED_ANCHORS" in (trace[0].get("unsupported_reason") or "")
    assert trace[0]["actual_system_protocol_sha256"] == \
        __import__("hashlib").sha256(_FR_PROTO.encode()).hexdigest()[:16]
    assert done["validation"]["repairs_used"] == 1
    assert done["validation"]["result"]["ok"] is True


def test_f2_unresolved_anchor_local_patch_system_never_reaches_model():
    bad = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    evs, chat = _run_lp("言必有中出处", _TOOLS_SCRIPT + [_msg(bad), _msg(_GOOD)],
                        adapter=_AnchorMissingAdapter())
    # 任何一次 LLM invocation 的输入都不得含 LOCAL_PATCH System
    for inv in chat.seen:
        blob = "".join(m["content"] for m in inv)
        assert _LP_PROTO not in blob
    # 修复 invocation 含 FULL_REWRITE protocol（互斥注入的另一面）
    assert any(_FR_PROTO in m["content"] for inv in chat.seen for m in inv)


# ═══════════════════════════════════════════════════════
# F3-F6: finalization 真实执行（repair 轮内新工具 → raw log 变更 →
# _stream_graph no_tools → pending 收口 patch → 真实 apply）
# ═══════════════════════════════════════════════════════
# RCA-2 起 quote 上 REPLACE_TEXT 非法——finalization patch 用 PARAPHRASE_CLAIM
# （纯转述, 无任何引号 → 不触发 PARAPHRASE_CONTAINS_VERBATIM_QUOTE 门）
_FIN_PATCH = json.dumps(
    {"patches": [{"issue_id": "vi_1", "action": "PARAPHRASE_CLAIM",
                  "replacement_text": "孔子在此批评鲁人改建长府，并借闵子骞之言说明"
                                      "行事应遵循成规，言语贵在切中要害。"}]},
    ensure_ascii=False)


def _finalization_run():
    bad = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    script = _TOOLS_SCRIPT + [
        _msg(bad),                                       # 初检 FAIL（伪引文）
        _msg("引文措辞需要再核。",
             [{"name": "get_chapter", "args": {"book_id": "lunyu", "chapter_idx": 14},
               "id": "r1"}]),                            # repair 轮内新工具执行
                                                       # （idx=14: 与初轮不同参数——
                                                       # 同参会被 DuplicateGuard
                                                       # 机械复用, raw log 不增长）
        _msg("已重新取得原文，输出修订。"),                  # repair 轮收口文本（将被丢弃）
        _msg(_FIN_PATCH),                                # finalization patch JSON
    ]
    return _run_lp("言必有中出处", script, adapter=LocalPatchAdapter())


def test_f3_finalization_tool_use_path_actually_executes():
    evs, chat = _finalization_run()
    done = _done(evs)
    trace = _trace(evs)
    assert len(trace) == 1
    assert trace[0]["repair_output_mode"] == "LOCAL_PATCH"
    fin = trace[0].get("finalization")
    assert fin and fin.get("raw_log_changed") is True
    assert fin.get("applied") is True
    assert fin.get("patch_chars", 0) > 0
    # 真实 apply 的证据: 伪引文 claim 被整体降级为转述 → validator PASS → 发布
    assert done["validation"]["repairs_used"] == 1     # finalization 不增 repairs
    assert done["validation"]["result"]["ok"] is True
    assert "切中要害" in _answer_text(evs)
    # case_result 口径: 恰 1 次 finalization invocation
    r = case_result("f3", evs)
    assert r["PATCH_FINALIZATION_INVOCATIONS"] == 1


def test_f4_finalization_candidate_captured_from_pending_not_token_event():
    evs, _chat = _finalization_run()
    fin = _trace(evs)[0]["finalization"]
    # patch_from=pending 且非空——旧「监听 token 事件」实现永远得空串
    assert fin.get("patch_from") == "pending"
    assert fin.get("patch_chars", 0) > 0
    assert fin.get("applied") is True


def test_f5_finalization_model_input_has_local_patch_system():
    evs, chat = _finalization_run()
    fin_inv = chat.seen[-1]                            # 最后一次 invocation = finalization
    blob = "".join(m["content"] for m in fin_inv)
    assert _LP_PROTO in blob
    assert _FR_PROTO not in blob
    assert any("Evidence refreshed" in m["content"]
               for m in fin_inv if m["role"] == "human")


def test_f6_finalization_tool_calls_zero():
    evs, _chat = _finalization_run()
    fin = _trace(evs)[0]["finalization"]
    assert fin.get("tool_calls") == 0
    r = case_result("f6", evs)
    assert r["FINALIZATION_TOOL_CALLS"] == 0


# ═══════════════════════════════════════════════════════
# F7/F8: terminal fingerprint（validation.history 真源）→ R1/R2 分类
# ═══════════════════════════════════════════════════════
_FAKE_B = "言必有中者，以其德风草偃之至也。闵子骞斯可谓中矣"


def test_f7_terminal_validation_fingerprint_recorded():
    # 不注入 adapter——repair 轮输出按全量候选解析（FULL_REWRITE 语义）,
    # 三个 validation state: 伪引文 A → 伪引文 B → 干净终态
    bad_a = "> 「" + _SENTINEL_FAKE + "」"
    bad_b = "> 「" + _FAKE_B + "」"
    script = _TOOLS_SCRIPT + [_msg(bad_a), _msg(bad_b), _msg(_GOOD)]
    _LP_OFF = getattr(EG, "LOCAL_PATCH_PRODUCTION_ENABLED", None)
    EG.LOCAL_PATCH_PRODUCTION_ENABLED = False   # 需要 FULL_REWRITE 全量候选修复语义
    try:
        evs, _chat = _run_lp("言必有中出处", script, adapter=None)
    finally:
        EG.LOCAL_PATCH_PRODUCTION_ENABLED = _LP_OFF
    hist = _done(evs)["validation"]["history"]
    assert len(hist) == 3                              # initial / after R1 / terminal
    for h in hist:
        assert isinstance(h.get("issue_fingerprints"), list)
    assert hist[0]["issue_fingerprints"]               # 初检有伪引文指纹
    assert hist[2]["issue_fingerprints"] == []         # terminal PASS → 空集


def test_f8_two_repairs_produce_r1_and_r2_classifications():
    bad_a = "> 「" + _SENTINEL_FAKE + "」"
    bad_b = "> 「" + _FAKE_B + "」"
    script = _TOOLS_SCRIPT + [_msg(bad_a), _msg(bad_b), _msg(_GOOD)]
    _LP_OFF = getattr(EG, "LOCAL_PATCH_PRODUCTION_ENABLED", None)
    EG.LOCAL_PATCH_PRODUCTION_ENABLED = False   # 需要 FULL_REWRITE 全量候选修复语义
    try:
        evs, _chat = _run_lp("言必有中出处", script, adapter=None)
    finally:
        EG.LOCAL_PATCH_PRODUCTION_ENABLED = _LP_OFF
    hist = _done(evs)["validation"]["history"]
    cls = classify_history(hist)
    assert set(cls) == {"R1", "R2"}
    # R1: 伪引文 A 消失、B 引入; R2: B 消失（fingerprint 集合差, 真源=history）
    assert cls["R1"]["resolved"] == hist[0]["issue_fingerprints"]
    assert cls["R1"]["introduced"] == hist[1]["issue_fingerprints"]
    assert cls["R2"]["resolved"] == sorted(
        set(hist[1]["issue_fingerprints"]) - set(hist[2]["issue_fingerprints"]))
    assert cls["R2"]["resolved"]                       # B 的指纹确实在 R2 被修掉
    assert cls["R2"]["introduced"] == []               # 干净终态零新指纹


# ═══════════════════════════════════════════════════════
# F9/F10: trace protocol SHA 按实际注入 mode 记录
# ═══════════════════════════════════════════════════════
def test_f9_local_patch_trace_hashes_local_protocol():
    import hashlib
    evs, _chat = _finalization_run()
    r = case_result("f9", evs)
    t = _trace(evs)[0]
    assert t["repair_output_mode"] == "LOCAL_PATCH"
    assert t["actual_system_protocol_sha256"] == \
        hashlib.sha256(_LP_PROTO.encode()).hexdigest()[:16]
    assert r["LOCAL_PATCH_TRACE_PROTOCOL_SHA_CORRECT"] is True


def test_f10_full_rewrite_trace_hashes_full_rewrite_protocol():
    import hashlib
    bad = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    evs, _chat = _run_lp("言必有中出处", _TOOLS_SCRIPT + [_msg(bad), _msg(_GOOD)],
                         adapter=_AnchorMissingAdapter())
    r = case_result("f10", evs)
    t = _trace(evs)[0]
    assert t["repair_output_mode"] == "FULL_REWRITE"
    assert t["actual_system_protocol_sha256"] == \
        hashlib.sha256(_FR_PROTO.encode()).hexdigest()[:16]
    assert t["actual_system_protocol_sha256"] != \
        hashlib.sha256(_LP_PROTO.encode()).hexdigest()[:16]
    assert r["FULL_REWRITE_TRACE_PROTOCOL_SHA_CORRECT"] is True


# ═══════════════════════════════════════════════════════
# F11/F12: 终态候选空 ≠ 未发布（两个独立机械事实）
# ═══════════════════════════════════════════════════════
def test_f11_terminal_nonempty_invalid_candidate_is_not_empty_candidate():
    bad = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    script = _TOOLS_SCRIPT + [_msg(bad), _msg(bad), _msg(bad)]   # 2 repair 全败
    evs, _chat = _run_lp("言必有中出处", script, adapter=LocalPatchAdapter())
    r = case_result("f11", evs)
    assert r["published"] is False
    # 终态候选有实质内容（被拒的是无效, 不是空）
    assert r["TERMINAL_CANDIDATE_EMPTY"] is False
    # 对照组: 终态候选真空 → True
    synthetic = [{"type": "done", "validation": {
        "history": [{"candidate_chars": 35}, {"candidate_chars": 0}],
        "result": {"ok": False, "issues": []}, "repair_trace": []}}]
    assert case_result("f11b", synthetic)["TERMINAL_CANDIDATE_EMPTY"] is True


def test_f12_unpublished_response_is_not_terminal_candidate_empty():
    bad = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    script = _TOOLS_SCRIPT + [_msg(bad), _msg(bad), _msg(bad)]
    evs, _chat = _run_lp("言必有中出处", script, adapter=LocalPatchAdapter())
    r = case_result("f12", evs)
    # validator 拒绝发布（无公开 token）≠ Main Agent 产出了空终态候选
    assert r["PUBLIC_RESPONSE_EMITTED"] is False
    assert r["TERMINAL_CANDIDATE_EMPTY"] is False
    assert r["published"] is False


# ═══════════════════════════════════════════════════════
# 漂移守卫: engine._issue_fingerprint ≡ repair_context.issue_fingerprint
# （engine 禁 import repair_context——H2-24; 算法一致性由本测试锁死）
# ═══════════════════════════════════════════════════════
def test_engine_fingerprint_matches_repair_context():
    for args in [("UNSUPPORTED_EXACT_QUOTE", "某引文预览文本", "qb_read_1"),
                 ("UNVERIFIED_CITATION", "【《论语》·先进篇】", "ev_3"),
                 ("NEAR_QUOTE_NOT_MARKED", "「引文」", None),
                 ("X", "", None)]:
        assert EG._issue_fingerprint(*args) == RC.issue_fingerprint(*args)
