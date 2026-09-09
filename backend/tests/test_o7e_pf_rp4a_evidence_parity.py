# -*- coding: utf-8 -*-
"""O7-E PF-RP4A Judge Evidence Parity: M1-M5 回归（真实 SCHOL_CAL2 artifact）。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import quote_bound as QB

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools", "evaluation"))
import o7e_bakeoff_judge2 as J2

_ART = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "docs/evidence/o7e_calib_SCHOL_CAL2.json")


def _case(cid):
    runs = json.load(open(_ART, encoding="utf-8"))
    return next(r for r in runs if r["case_id"] == cid)


def _joined_windows(r):
    windows, _meta = J2._replay_windows(r)
    return "".join(w["source_window"] for w in windows), windows


def test_m1_h13_heidegger_sentence_replayed():
    h13 = _case("H13")
    assert "c5013f33fe01#4" in ((h13.get("evidence_digest") or {})
                                .get("facts", {}).get("read_chapters") or [])
    joined, _w = _joined_windows(h13)
    assert "无世界的单纯主体" in joined, "H13 被judge指控伪造的句子必须出现在 replay 中"


def test_m2_h07_locke_sentence_replayed():
    h07 = _case("H07")
    assert "44a32441dabe#31" in ((h07.get("evidence_digest") or {})
                                 .get("facts", {}).get("read_chapters") or [])
    joined, _w = _joined_windows(h07)
    assert "組織适当的身体" in joined, "H07 被judge判 FALSE_EXACT_QUOTE 的原句必须在 replay 中"


def test_m3_scare_quotes_never_crowd_out_textual_claims():
    """候选=全部 quote spans + substantial claims; 截断只发生在全量排序之后,
    且 top-K 上限 24——前 12 个 scare quotes 不能挤掉后面的长 textual claim。"""
    h13 = _case("H13")
    windows, meta = J2._replay_windows(h13)
    assert meta["primary_replay_candidates"] > 12          # 候选远多于旧 [:12]
    assert len(windows) <= 24                              # bounded top-K
    # 排序性质: windows 的 overlap 单调不增
    ovs = [w["overlap"] for w in windows]
    assert ovs == sorted(ovs, reverse=True)
    assert meta["primary_replay_coverage_rate"] > 0


def test_m4_replay_sources_subset_of_recorded_chapters():
    for cid in ("H13", "H07", "H04", "S4", "S7", "H02", "H03"):
        r = _case(cid)
        windows, meta = J2._replay_windows(r)
        recorded = set((r.get("evidence_digest") or {})
                       .get("facts", {}).get("read_chapters") or [])
        assert all(w["chapter_key"] in recorded for w in windows), cid
        assert meta["new_primary_source_ids"] == 0         # M5


def test_m5_compact_digest_structured_not_blind_truncated():
    d = J2._compact_digest(_case("H13"))
    assert isinstance(d, dict) and "used_evidence" in d
    assert isinstance(d["used_evidence"], list)
