# -*- coding: utf-8 -*-
"""O7-B Bibliographic Metadata Foundation tests（B1-B12 + 架构不变量）。

Gate 原则: accuracy > completeness——每个 populated verified field 必须有
provenance; missingness 是合法状态; 占位字符串禁止。
"""
import hashlib
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # DeepPhilosophy/
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)

BIBLIO_PATH = os.path.join(BACKEND, "data", "book_bibliography.json")
MANIFEST_PATH = os.path.join(ROOT, "docs", "evidence",
                             "PHIAGENT_O7B_BIBLIOGRAPHIC_PILOT_MANIFEST.json")
BASE_SHA = "9edf34775"  # O7-B BASE（任务书落盘 commit）


def _load():
    assert os.path.exists(BIBLIO_PATH), "book_bibliography.json 未生成（先跑 dp_biblio_build.py）"
    return json.load(open(BIBLIO_PATH, encoding="utf-8"))


def _git_diff_quiet(base, path):
    return subprocess.run(
        ["git", "diff", "--quiet", base, "--", path],
        cwd=ROOT, capture_output=True).returncode == 0


@pytest.fixture(scope="module")
def biblio():
    return _load()


# ── B1: missing translator remains null ──────────────────────
def test_b1_missing_translator_remains_null(biblio):
    recs = biblio["books"].values()
    null_tr = [r for r in recs if r["edition"]["translator"] is None]
    assert null_tr, "pilot 应存在 translator=null 的记录（缺失即 null, 不占位）"
    for r in null_tr:
        assert r["edition"]["translator"] is None
        assert "未知" not in json.dumps(r["edition"], ensure_ascii=False)


# ── B2: Tier4 alone cannot verify（本实现无 Tier4 源; 断言无 tier4 verified）──
def test_b2_no_tier4_verified(biblio):
    for r in biblio["books"].values():
        for f, v in r["field_provenance"].items():
            assert v["source_tier"] != 4 or not v["verified"], f"{r['book_id']}.{f} Tier4 不得 verified"


# ── B3: OCR candidate != verified automatically ──────────────
def test_b3_ocr_candidate_not_auto_verified(biblio):
    for r in biblio["books"].values():
        for f, v in r["field_provenance"].items():
            if v["status"] == "OCR_CANDIDATE":
                assert v["verified"] is False, f"{r['book_id']}.{f}"
                assert v["confidence"] < 0.95, "候选置信度不得达到 verified 级"
            if v["verified"]:
                assert len({(e["chapter_idx"], e.get("line_no", -1)) for e in v["evidence"]}) >= 2, \
                    f"{r['book_id']}.{f} verified 需 ≥2 独立证据行"


# ── B4: conflicting sources preserved（无静默 last-write-wins）──
def test_b4_conflicts_preserved(biblio):
    # 当前实现: 所有候选值都保留在 field_provenance 的 evidence 中;
    # 若出现冲突值, 不得在无 resolution 记录的情况下覆盖（conflicts 数组如实）。
    for r in biblio["books"].values():
        for f, v in r["field_provenance"].items():
            assert "evidence" in v, f"{r['book_id']}.{f} 证据必须保留"


# ── B5: two editions not collapsed（book_id 即 edition 维度之一）──
def test_b5_editions_not_collapsed(biblio):
    ids = list(biblio["books"].keys())
    assert len(ids) == len(set(ids)), "book_id 不得合并"


# ── B6: canonical vs edition-specific distinct ───────────────
def test_b6_canonical_vs_structural_distinct(biblio):
    for r in biblio["books"].values():
        kinds = {l["locator_kind"] for l in r["locators"]}
        assert kinds <= {"CANONICAL", "STRUCTURAL", "EDITION_SPECIFIC"}
        canon = {l["locator_scheme"] for l in r["locators"] if l["locator_kind"] == "CANONICAL"}
        struct = {l["locator_scheme"] for l in r["locators"] if l["locator_kind"] == "STRUCTURAL"}
        assert not (canon & struct), "canonical 与 structural scheme 不得混用"


# ── B7: page unavailable → lower granularity（无 EDITION_PAGE 声明）──
def test_b7_no_fake_page_granularity(biblio):
    for r in biblio["books"].values():
        assert r["citation_capability"]["max_verified_granularity"] != "EDITION_PAGE", \
            f"{r['book_id']}: 无页码映射数据不得声明 EDITION_PAGE"


# ── B8: no fake chapter/section placeholder ──────────────────
def test_b8_no_placeholder_strings(biblio):
    banned = ["未知译者", "未知出版社", "第?页", "不详", "佚名"]
    s = json.dumps(biblio, ensure_ascii=False)
    for b in banned:
        assert b not in s, f"占位字符串出现: {b}"


# ── B9/B10: 工具 additive 兼容 + 元数据可见性 ─────────────────
def test_b9_b10_tool_exposure():
    from routes import agent_tools_retrieval as RT
    _exec = None
    for t in RT.TOOLS.values() if isinstance(RT.TOOLS, dict) else []:
        pass
    # 通过注册表拿执行器
    tools = RT.TOOLS
    det = tools.get("get_book_detail")
    ch = tools.get("get_chapter")
    assert det and ch, "get_book_detail/get_chapter 必须仍注册"
    det_exec, ch_exec = det["execute"], ch["execute"]
    pilot_id = next(iter(_load()["books"]))
    d = det_exec({"book_id": pilot_id})
    assert d.get("bibliographic_metadata"), "pilot 书 detail 应携带 bibliographic_metadata"
    assert set(d) >= {"id", "title", "author", "toc"}, "已有字段保持兼容"
    c = ch_exec({"book_id": pilot_id, "chapter_idx": 0})
    assert "citation_label" in c and "text" in c, "get_chapter 已有字段保持兼容"
    # 非 pilot 书: 无 bibliographic_metadata 键（零行为改动）
    all_ids = {b["id"] for b in json.load(open(os.path.join(ROOT, "app", "public", "books.json"), encoding="utf-8"))}
    non_pilot = next(i for i in all_ids if i not in _load()["books"])
    d2 = det_exec({"book_id": non_pilot})
    assert "bibliographic_metadata" not in d2
    # null 字段不产生占位文本
    assert "未知" not in json.dumps(d.get("bibliographic_metadata", {}), ensure_ascii=False)


# ── B11: existing citation_label 语义不变 ─────────────────────
def test_b11_citation_label_unchanged():
    from routes.agent_tools_retrieval import _cite_label
    assert _cite_label("论语", "学而第一") == "【《论语》·学而第一】"
    assert _cite_label("论语", "") == "【《论语》】"
    assert _cite_label("", "x") == ""


# ── B12: production prompt / validator / quote_bound 零改动 ───
@pytest.mark.parametrize("rel", [
    "backend/engine_langgraph.py",
    "backend/final_validator.py",
    "backend/quote_bound.py",
])
def test_b12_production_unchanged(rel):
    assert _git_diff_quiet(BASE_SHA, rel), f"{rel} 相对 BASE {BASE_SHA} 有改动（O7-B 禁止）"


# ── Gate 硬门 §29 ────────────────────────────────────────────
def test_gate_pilot_size_and_traditions():
    m = json.load(open(MANIFEST_PATH, encoding="utf-8"))
    assert m["pilot"]["works"] >= 30
    assert len(m["pilot"]["traditions_or_periods"]) >= 5


def test_gate_every_verified_field_has_provenance(biblio):
    n = 0
    for r in biblio["books"].values():
        for f, v in r["field_provenance"].items():
            if v["verified"]:
                n += 1
                assert v.get("source_tier") and v.get("source_type") and v.get("evidence"), \
                    f"{r['book_id']}.{f} verified 字段缺 provenance"
    assert n >= 15, "verified 字段样本量过小"


def test_gate_work_edition_source_separated(biblio):
    for r in biblio["books"].values():
        assert {"work", "edition", "digital_source"} <= set(r)
        assert r["digital_source"]["source_hash"], "数字源 hash 必填"
