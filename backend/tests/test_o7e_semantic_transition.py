# -*- coding: utf-8 -*-
"""V7-F2-R1: 语义转移分类器 + per-round semantic snapshot 确定性测试。

Reviewer R1 任务书（2026-09-11）要求的五类场景 A-E + issue-code relabel +
AMBIGUOUS fail-closed + 8 字段 snapshot schema 合同。全部确定性（无 LLM、
无网络、无随机）; F 系列为 production path 集成（真实 LangGraph 图 +
脚本化假 LLM, 与 test_o7e_final_diagnostic 同一 harness）。
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import o7e_semantic_transition as ST
import engine_langgraph as EG

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_o7e_final_diagnostic import (_run_lp, _done, _GOOD,
                                       _AnchorMissingAdapter)
from test_o2_final_ownership import _TOOLS_SCRIPT, _msg, _SENTINEL_FAKE


# ── 快照构造 helper（与 engine._issue_snapshot 同 schema 的最小手写版）────
def _snap(round_id, fp, code, locator, ev=None, fam=None, nloc=None,
          srid=None, cqt=None):
    return {
        "round_id": round_id,
        "fingerprint": fp,
        "issue_code": code,
        "semantic_family": fam if fam is not None else ST.semantic_family(code),
        "normalized_locator": nloc if nloc is not None else ST.normalize_locator(locator),
        "evidence_ref": ev,
        "source_record_id": srid,
        "citation_or_quote_target_id": cqt,
    }


def _fp(code, locator, ev=None):
    import hashlib
    import quote_bound as QB
    return hashlib.sha256(
        f"{code}|{QB.norm_q(locator or '')[:120]}|{ev or ''}".encode()
    ).hexdigest()[:16]


_CITE_A = "【《从〈理想国〉到〈正义论〉》·卢梭：《社会契约论》】"
_CITE_B = "【《《真理与方法》解读》·第二章】"


# ═══════════════════════════════════════════════════════
# A. 完全相同 issue → PERSISTED
# ═══════════════════════════════════════════════════════
def test_a_identical_issue_persisted():
    prev = [_snap(0, _fp("UNVERIFIED_CITATION", _CITE_A), "UNVERIFIED_CITATION",
                  _CITE_A, ev=None)]
    cur = [_snap(1, _fp("UNVERIFIED_CITATION", _CITE_A), "UNVERIFIED_CITATION",
                 _CITE_A, ev=None)]
    r = ST.classify_transition(prev, cur)
    assert r["summary"]["PERSISTED"] == 1
    assert r["summary"]["RESOLVED"] == 0
    assert r["introduced_class"] == {}
    assert not ST.transition_is_fail_closed(r["summary"])


# ═══════════════════════════════════════════════════════
# B. 同 issue 仅文本位置合理移动 → LOCATOR_SHIFT_ONLY
# ═══════════════════════════════════════════════════════
def test_b_locator_shift_only():
    loc_prev = "“人是生而自由的,但却无往不在枷锁之中”——《社会契约论》第一卷第一章"
    loc_cur = "“人是生而自由的,但却无往不在枷锁之中”——《社会契约论》第一卷第四章"
    prev = [_snap(0, _fp("UNSUPPORTED_EXACT_QUOTE", loc_prev, "ev_3"),
                  "UNSUPPORTED_EXACT_QUOTE", loc_prev, ev="ev_3")]
    cur = [_snap(1, _fp("UNSUPPORTED_EXACT_QUOTE", loc_cur, "ev_3"),
                 "UNSUPPORTED_EXACT_QUOTE", loc_cur, ev="ev_3")]
    r = ST.classify_transition(prev, cur)
    assert r["summary"]["LOCATOR_SHIFT_ONLY"] == 1
    assert r["summary"]["GENUINELY_NEW_ISSUE"] == 0
    assert r["summary"]["AMBIGUOUS"] == 0
    assert r["successor_of"] and list(r["successor_of"].values()) == [prev[0]["fingerprint"]]


# ═══════════════════════════════════════════════════════
# C. 同 semantic target 但 fingerprint 改变 → SAME_ISSUE_REKEYED
# ═══════════════════════════════════════════════════════
def test_c_same_target_rekeyed():
    # 同 code + 同 locator（归一后逐字相同）, 仅 evidence_ref 变 → 指纹变
    prev = [_snap(0, _fp("UNVERIFIED_CITATION", _CITE_A, "ev_1"),
                  "UNVERIFIED_CITATION", _CITE_A, ev="ev_1")]
    cur = [_snap(1, _fp("UNVERIFIED_CITATION", _CITE_A, "ev_9"),
                 "UNVERIFIED_CITATION", _CITE_A, ev="ev_9")]
    assert prev[0]["fingerprint"] != cur[0]["fingerprint"]
    r = ST.classify_transition(prev, cur)
    assert r["summary"]["SAME_ISSUE_REKEYED"] == 1
    assert r["summary"]["RESOLVED"] == 0
    assert r["summary"]["AMBIGUOUS"] == 0


# ═══════════════════════════════════════════════════════
# D. repair 真正制造另一 violation → GENUINELY_NEW_ISSUE
# ═══════════════════════════════════════════════════════
def test_d_genuinely_new_issue():
    prev = [_snap(0, _fp("UNVERIFIED_CITATION", _CITE_A), "UNVERIFIED_CITATION",
                  _CITE_A)]
    new_loc = "“凡是不能杀死你的,终将使你更强大” 斯宾格勒《西方的没落》章二"
    cur = [_snap(1, _fp("STITCHED_QUOTE", new_loc, "ev_5"),
                 "STITCHED_QUOTE", new_loc, ev="ev_5")]
    r = ST.classify_transition(prev, cur)
    assert r["summary"]["GENUINELY_NEW_ISSUE"] == 1
    assert r["summary"]["RESOLVED"] == 1   # 旧 issue 无语义后继 → 真消失
    assert r["summary"]["AMBIGUOUS"] == 0


# ═══════════════════════════════════════════════════════
# E. 无法可靠匹配 → AMBIGUOUS（fail-closed）
# ═══════════════════════════════════════════════════════
def test_e1_insufficient_identity_ambiguous():
    # EMPTY_FINAL: locator 空 + evidence_ref null → 身份不完整, 不得猜
    prev = [_snap(0, _fp("UNSUPPORTED_EXACT_QUOTE", "某段引文"), "UNSUPPORTED_EXACT_QUOTE",
                  "某段引文")]
    cur = [_snap(1, _fp("EMPTY_FINAL", ""), "EMPTY_FINAL", "", ev=None)]
    r = ST.classify_transition(prev, cur)
    assert r["summary"]["AMBIGUOUS"] == 1
    assert r["summary"]["GENUINELY_NEW_ISSUE"] == 0
    assert ST.transition_is_fail_closed(r["summary"])


def test_e2_competing_candidates_ambiguous():
    # 两个等强（同分）竞争候选 → 无法唯一归因 → AMBIGUOUS
    prev = [_snap(0, _fp("UNSUPPORTED_EXACT_QUOTE", "甲乙丙丁", "ev_2"),
                  "UNSUPPORTED_EXACT_QUOTE", "甲乙丙丁", ev="ev_2"),
            _snap(0, _fp("UNSUPPORTED_EXACT_QUOTE", "甲乙丙戊", "ev_2"),
                  "UNSUPPORTED_EXACT_QUOTE", "甲乙丙戊", ev="ev_2")]
    cur = [_snap(1, _fp("UNSUPPORTED_EXACT_QUOTE", "甲乙丙己", "ev_2"),
                 "UNSUPPORTED_EXACT_QUOTE", "甲乙丙己", ev="ev_2")]
    r = ST.classify_transition(prev, cur)
    assert r["summary"]["AMBIGUOUS"] == 1
    assert r["successor_of"] == {}


def test_e3_gray_zone_overlap_ambiguous():
    # 同 code 同 ev, 词汇重合落灰区 [0.3, 0.5) → 不猜, AMBIGUOUS
    prev = [_snap(0, _fp("UNSUPPORTED_EXACT_QUOTE", "天地玄黄宇宙洪荒", "ev_4"),
                  "UNSUPPORTED_EXACT_QUOTE", "天地玄黄宇宙洪荒", ev="ev_4")]
    cur = [_snap(1, _fp("UNSUPPORTED_EXACT_QUOTE", "宇宙洪荒日月盈昃", "ev_4"),
                 "UNSUPPORTED_EXACT_QUOTE", "宇宙洪荒日月盈昃", ev="ev_4")]
    ov = ST._overlap(ST._words(prev[0]["normalized_locator"]),
                     ST._words(cur[0]["normalized_locator"]))
    assert ST._LOCATOR_OVERLAP_GRAY <= ov < ST._LOCATOR_OVERLAP_MATCH
    r = ST.classify_transition(prev, cur)
    assert r["summary"]["AMBIGUOUS"] == 1
    assert r["summary"]["GENUINELY_NEW_ISSUE"] == 0


def test_e4_double_component_change_ambiguous():
    # locator 与 evidence_ref 同时改变（同 code）→ 无法归因, fail-closed
    loc_p, loc_c = "“知人者智,自知者明”第一章", "“知人者智,自知者明”第九章"
    prev = [_snap(0, _fp("UNSUPPORTED_EXACT_QUOTE", loc_p, "ev_1"),
                  "UNSUPPORTED_EXACT_QUOTE", loc_p, ev="ev_1")]
    cur = [_snap(1, _fp("UNSUPPORTED_EXACT_QUOTE", loc_c, "ev_7"),
                 "UNSUPPORTED_EXACT_QUOTE", loc_c, ev="ev_7")]
    r = ST.classify_transition(prev, cur)
    assert r["summary"]["AMBIGUOUS"] == 1


def test_e5_null_fingerprint_fail_closed():
    # 指纹显式 null（schema 允许）→ 不可集合追踪 → AMBIGUOUS, 不得静默
    prev = [_snap(0, None, "UNVERIFIED_CITATION", _CITE_A)]
    cur = [_snap(1, None, "UNVERIFIED_CITATION", _CITE_A)]
    r = ST.classify_transition(prev, cur)
    assert r["summary"]["AMBIGUOUS"] >= 1
    assert ST.transition_is_fail_closed(r["summary"])


# ═══════════════════════════════════════════════════════
# issue-code relabel（同家族 + 同目标文本, 校验器改名）
# ═══════════════════════════════════════════════════════
def test_f_issue_code_relabel():
    loc = "“绝对精神是自我意识的完成” section 3 paragraph 12 end"
    prev = [_snap(0, _fp("UNSUPPORTED_EXACT_QUOTE", loc, "ev_6"),
                  "UNSUPPORTED_EXACT_QUOTE", loc, ev="ev_6")]
    cur = [_snap(1, _fp("NEAR_QUOTE_NOT_MARKED", loc, "ev_6"),
                 "NEAR_QUOTE_NOT_MARKED", loc, ev="ev_6")]
    r = ST.classify_transition(prev, cur)
    assert r["summary"]["ISSUE_CODE_RELABEL"] == 1
    assert r["summary"]["GENUINELY_NEW_ISSUE"] == 0
    assert r["summary"]["AMBIGUOUS"] == 0


# ═══════════════════════════════════════════════════════
# 8 字段 snapshot schema 合同（engine._issue_snapshot）
# ═══════════════════════════════════════════════════════
_SNAPSHOT_KEYS = {"round_id", "fingerprint", "issue_code", "semantic_family",
                  "normalized_locator", "evidence_ref", "source_record_id",
                  "citation_or_quote_target_id"}


def test_g_snapshot_schema_complete_explicit_nulls():
    # validator 不产 source/citation target id → 必须显式 null（键不得缺失）
    snap = EG._issue_snapshot(0, {"code": "UNVERIFIED_CITATION",
                                  "locator": _CITE_A, "evidence_ref": None})
    assert set(snap.keys()) == _SNAPSHOT_KEYS
    assert snap["source_record_id"] is None
    assert snap["citation_or_quote_target_id"] is None
    assert snap["round_id"] == 0
    assert snap["issue_code"] == "UNVERIFIED_CITATION"
    assert snap["semantic_family"] == "CITATION"
    assert snap["fingerprint"] == EG._issue_fingerprint("UNVERIFIED_CITATION",
                                                        _CITE_A, None)
    assert len(snap["normalized_locator"]) <= 200
    # 全部值为有界标量（无 CoT/正文/嵌套大对象）
    assert all(v is None or isinstance(v, (str, int)) for v in snap.values())


def test_g2_snapshot_never_throws_on_null_issue():
    snap = EG._issue_snapshot(3, None)
    assert set(snap.keys()) == _SNAPSHOT_KEYS
    assert snap["fingerprint"] == EG._issue_fingerprint(None, "", None)


def test_g3_semantic_family_closed_set():
    assert ST.semantic_family("UNVERIFIED_CITATION") == "CITATION"
    assert ST.semantic_family("UNSUPPORTED_EXACT_QUOTE") == "QUOTE"
    assert ST.semantic_family("NEAR_QUOTE_NOT_MARKED") == "QUOTE"
    assert ST.semantic_family("STITCHED_QUOTE") == "QUOTE"
    assert ST.semantic_family("EMPTY_FINAL") == "EMPTY"
    assert ST.semantic_family("UNGROUNDED_BIBLIOGRAPHIC_DETAIL") == "BIBLIOGRAPHIC"
    assert ST.semantic_family(None) is None
    # 未知码确定性降级（不抛异常、不猜封闭家族）
    assert ST.semantic_family("SOME_FUTURE_CODE") == "SOME"


# ═══════════════════════════════════════════════════════
# 六项 DEV 计数聚合 + fail-closed 语义
# ═══════════════════════════════════════════════════════
def test_h_dev_probe_counts_aggregation():
    counts = ST.dev_probe_counts([
        {"RESOLVED": 1, "PERSISTED": 0, "GENUINELY_NEW_ISSUE": 0,
         "SAME_ISSUE_REKEYED": 1, "LOCATOR_SHIFT_ONLY": 0,
         "ISSUE_CODE_RELABEL": 0, "AMBIGUOUS": 0},
        {"RESOLVED": 0, "PERSISTED": 0, "GENUINELY_NEW_ISSUE": 0,
         "SAME_ISSUE_REKEYED": 0, "LOCATOR_SHIFT_ONLY": 1,
         "ISSUE_CODE_RELABEL": 0, "AMBIGUOUS": 0},
    ])
    assert counts == {"NEW_FINGERPRINT_COUNT": 2, "GENUINELY_NEW_ISSUE_COUNT": 0,
                      "REKEY_COUNT": 1, "LOCATOR_SHIFT_COUNT": 1,
                      "RELABEL_COUNT": 0, "AMBIGUOUS_COUNT": 0}


def test_h2_ambiguous_never_downgraded():
    # AMBIGUOUS 是终态标签: fail-closed 判定只能由 AMBIGUOUS 计数触发,
    # 且 classify_transition 任何路径都不产生第七类以外的标签
    r = ST.classify_transition(
        [_snap(0, _fp("UNVERIFIED_CITATION", _CITE_B, "ev_17"),
               "UNVERIFIED_CITATION", _CITE_B, ev="ev_17")],
        [_snap(1, None, None, "", ev=None)])
    assert r["summary"]["AMBIGUOUS"] >= 1
    for label in r["introduced_class"].values():
        assert label in ST.LABELS
    assert ST.transition_is_fail_closed(r["summary"])


# ═══════════════════════════════════════════════════════
# F. production path 集成（真实 LangGraph 图 + 脚本化假 LLM）
# ═══════════════════════════════════════════════════════
def test_i_engine_persists_semantic_transition_per_round():
    bad = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
    # _AnchorMissingAdapter: LP anchors 不可解析 → supported=False → 走
    # FULL_REWRITE（与 test_o7e_final_diagnostic F1 同一 production harness）
    evs, _chat = _run_lp("言必有中出处",
                         _TOOLS_SCRIPT + [_msg(bad), _msg(_GOOD)],
                         adapter=_AnchorMissingAdapter())
    hist = _done(evs)["validation"]["history"]
    assert len(hist) >= 2
    # INITIAL 轮: 无 transition（显式 null）, 8 字段快照完整
    assert hist[0]["semantic_transition"] is None
    d0 = hist[0]["issue_details"][0]
    assert set(d0.keys()) == _SNAPSHOT_KEYS
    # R1 轮: bad→good → 旧 issue RESOLVED, 零 introduced, 零 AMBIGUOUS
    st1 = hist[1]["semantic_transition"]
    assert st1 is not None
    assert st1["summary"]["RESOLVED"] >= 1
    assert st1["summary"]["GENUINELY_NEW_ISSUE"] == 0
    assert st1["summary"]["AMBIGUOUS"] == 0
    # legacy fingerprint telemetry 原样保留（第二层, 不覆盖）
    assert hist[0]["issue_fingerprints"] and hist[0]["issue_codes"]
