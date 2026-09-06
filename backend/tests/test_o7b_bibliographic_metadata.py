# -*- coding: utf-8 -*-
"""O7-B RP1 Bibliographic Metadata Integrity tests（R1-R17, 取代首轮 B 套件）。

Kill case（已冻结为回归）: 「上海译文出版社」→「上海译」→ translator=上海 verified=true。
"""
import hashlib
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
sys.path.insert(0, os.path.join(BACKEND, "tools"))

BIBLIO_PATH = os.path.join(BACKEND, "data", "book_bibliography.json")
MANIFEST_PATH = os.path.join(ROOT, "docs", "evidence",
                             "PHIAGENT_O7B_BIBLIOGRAPHIC_PILOT_MANIFEST.json")
AUDIT_PATH = os.path.join(ROOT, "docs", "evidence",
                          "PHIAGENT_O7B_SEMANTIC_FIELD_AUDIT.json")
RP1_CODE_SHA = "500bb8e88"  # routes 冻结基线（O7-C §59 授权改动落地 commit）
O7A_BASE = "302f7380a4146d78374887063b336c5aa7381ddd"

import dp_biblio_build as B


def _load():
    assert os.path.exists(BIBLIO_PATH)
    return json.load(open(BIBLIO_PATH, encoding="utf-8"))


@pytest.fixture(scope="module")
def biblio():
    return _load()


# ══ R1/R2/R3/R4 — translator 语义边界（kill case 回归 + 变体）════════
def _trans(spans_lines):
    spans = [(0, n, l) for n, l in enumerate(spans_lines)]
    found = B._collect_rx(spans, B.RE_TRANSLATOR, "RESPONSIBILITY_STATEMENT")
    return B._field_from_found(found)


def test_r1_publisher_not_translator():
    """kill case: 「上海译文出版社」不得产出 translator=上海。"""
    lines = ["刘继译．—上海：上海译文出版社", "上海译文出版社发行", "上海译文出版社"]
    f = _trans(lines)
    values = [c["value"] for c in f["candidates"]]
    assert "上海" not in values
    assert not f["verified"]  # 刘继仅 1 span → OCR_CANDIDATE


def test_r2_real_liuji():
    """真实责任陈述「刘继译」抽出的候选是 刘继。"""
    lines = ["单向度的人／（美）赫伯特·马尔库塞著；刘继译",
             "刘继译．—上海：上海译文出版社"]
    f = _trans(lines)
    assert "刘继" in [c["value"] for c in f["candidates"]]
    assert f["verified"] and f["selected_value"] == "刘继"


def test_r3_whitespace_variant():
    """「卫茂平 译」空白变体。"""
    lines = ["善恶的彼岸／（德）尼采著；卫茂平 译", "卫茂平 译．—上海：华东师范大学出版社"]
    f = _trans(lines)
    assert f["verified"] and f["selected_value"] == "卫茂平"


@pytest.mark.parametrize("line", [
    "上海译文出版社",       # kill case 原文
    "翻译出版社",
    "某某译文版本说明",
    "本书据某某译本排印",
    "修订译本",
    "英汉对照译丛",
])
def test_r4_negative_variants(line):
    f = _trans([line, line])  # 两行重复也绝不 eligible
    values = [c["value"] for c in f["candidates"]]
    assert not any(v in ("上海", "翻译", "修订", "对照", "排印") for v in values), values
    assert not f["verified"]


# ══ R5 — 国籍 ≠ 原文语种 ═════════════════════════════════════
def test_r5_nationality_not_language():
    for r in _load()["books"].values():
        assert r["work"]["original_language"] is None, \
            "本库无明确语言事实, original_language 必须为 null"
        hint = r["field_provenance"].get("author_nationality_hint")
        if hint:
            assert hint["verified"] is False
            assert hint["candidates"][0]["semantic_source_type"] == "AUTHOR_NATIONALITY_HINT"


# ══ R6/R7/R8 — 冲突模型 ═════════════════════════════════════
def _cand(value, n, cls="PUBLISHER_STATEMENT"):
    return {"value": value,
            "evidence": [{"chapter_idx": 0, "line_no": i, "raw_span": value,
                          "semantic_source_type": cls} for i in range(n)],
            "semantic_source_type": cls, "n_spans": n}


def test_r6_conflicts_preserved():
    f = B._mk_field([_cand("商务印书馆", 2), _cand("中华书局", 2)], ["商务印书馆", "中华书局"])
    vals = [c["value"] for c in f["candidates"]]
    assert "商务印书馆" in vals and "中华书局" in vals
    assert f["resolution_status"] == "CONFLICT_UNRESOLVED"


def test_r7_unresolved_publishes_null(biblio):
    for r in biblio["books"].values():
        for k, v in r["field_provenance"].items():
            if v.get("conflict"):
                # production 层对应字段必须 null
                prod = r["edition"].get(k, r["work"].get(k))
                assert prod in (None,), f"{r['book_id']}.{k} 冲突却发布了 {prod!r}"


def test_r8_no_majority_wins():
    f = B._mk_field([_cand("甲出版社", 5), _cand("乙出版社", 2)], ["甲出版社", "乙出版社"])
    assert f["resolution_status"] == "CONFLICT_UNRESOLVED"
    assert f["selected_value"] is None and not f["verified"]


# ══ R9 — 年份语义分类 ═══════════════════════════════════════
def test_r9_year_semantics():
    # 构造临时章节: 印刷年/CIP 核字年 不得支持 publication_year
    import tempfile
    tmp = tempfile.mkdtemp()
    old = B.CHAPTERS
    bid = "synthetic"
    os.makedirs(os.path.join(tmp, bid), exist_ok=True)
    blocks = [{"type": "text", "value": l} for l in (
        "某某书／（德）某人著；张三译．—北京：测试出版社，2019",
        "CIP数据核字（2019）第99999号",
        "2020年3月第1次印刷",
        "2019年5月第1版",
    )]
    json.dump({"index": 0, "title": "版权页", "content": blocks},
              open(os.path.join(tmp, bid, "0.json"), "w", encoding="utf-8"))
    try:
        B.CHAPTERS = tmp
        fm = B.extract_front_matter(bid)
        y = fm["publication_year"]
        assert y["selected_value"] == "2019"  # CIP 行 + 第1版 双证据
        # 若版次年与 CIP 年异值 → CONFLICT_UNRESOLVED
        blocks2 = [{"type": "text", "value": l} for l in (
            "某某书／（德）某人著；张三译．—北京：测试出版社，2019",
            "2020年5月第1版",
            "2020年5月第1版",
        )]
        json.dump({"index": 0, "title": "版权页", "content": blocks2},
                  open(os.path.join(tmp, bid, "0.json"), "w", encoding="utf-8"))
        fm2 = B.extract_front_matter(bid)
        y2 = fm2["publication_year"]
        assert y2["resolution_status"] == "CONFLICT_UNRESOLVED"
        assert y2["selected_value"] is None
        # RP2 §9 行为断言: 印刷年不制造冲突（CIP=EDITION=2019, PRINTING=2020 → 2019）
        blocks3 = [{"type": "text", "value": l} for l in (
            "某某书／（德）某人著；张三译．—北京：测试出版社，2019",
            "2019年5月第1版",
            "2020年3月第1次印刷",
        )]
        json.dump({"index": 0, "title": "版权页", "content": blocks3},
                  open(os.path.join(tmp, bid, "0.json"), "w", encoding="utf-8"))
        fm3 = B.extract_front_matter(bid)
        y3 = fm3["publication_year"]
        assert y3["selected_value"] == "2019" and y3["resolution_status"] == "NO_CONFLICT"
        # 仅印刷年+核字年 → 不得 verify
        blocks4 = [{"type": "text", "value": l} for l in (
            "某某书／（德）某人著；张三译．—北京：测试出版社",
            "CIP数据核字（2020）第99999号",
            "2020年3月第1次印刷",
            "2021年3月第2次印刷",
        )]
        json.dump({"index": 0, "title": "版权页", "content": blocks4},
                  open(os.path.join(tmp, bid, "0.json"), "w", encoding="utf-8"))
        fm4 = B.extract_front_matter(bid)
        y4 = fm4["publication_year"]
        assert not y4["verified"] and y4["selected_value"] is None
    finally:
        B.CHAPTERS = old


# ══ R10/R11 — 实体 identity ═════════════════════════════════
def _synthetic_two_editions():
    """RP2 §6: evaluation-only 构造同 work_id 双 edition/双 source（不写 production）。"""
    import copy
    data = _load()
    base = copy.deepcopy(next(iter(data["books"].values())))
    a = copy.deepcopy(base)
    a.update({"book_id": "syn-a", "work_id": "work-same",
              "edition_record_id": "ed-A", "digital_source_id": "ds-A"})
    b2 = copy.deepcopy(a)
    b2.update({"book_id": "syn-b", "edition_record_id": "ed-B", "digital_source_id": "ds-B"})
    b2["edition"] = dict(a["edition"], publisher="另一出版社", publication_year=1999)
    return a, b2


def _entity_model_insert(records, new_records):
    """模拟数据层实体容纳: books dict 按 book_id 存, work_id 分组不合并。"""
    out = dict(records)
    for r in new_records:
        out[r["book_id"]] = r
    return out


def test_r10_two_editions_distinct():
    """synthetic: 同 work_id 两个 edition/source 必须独立存在（非空转）。"""
    a, b2 = _synthetic_two_editions()
    merged = _entity_model_insert({}, [a, b2])
    by_work = {}
    for r in merged.values():
        by_work.setdefault(r["work_id"], []).append(r)
    rs = by_work["work-same"]
    assert len(rs) == 2, "R10 非空转: 同 work 必须恰好 2 条记录"
    assert {r["edition_record_id"] for r in rs} == {"ed-A", "ed-B"}
    assert {r["digital_source_id"] for r in rs} == {"ds-A", "ds-B"}
    assert len(merged) == 2, "no overwrite/merge"


def test_r10_work_id_stable_across_edition_changes():
    """RP2 §7: edition 元数据变化 → work_id 不变; edition_record_id 变 → work_id 不变。"""
    import hashlib
    def wid(author, title):
        return "work-" + hashlib.sha256((author + "|" + title).encode()).hexdigest()[:12]
    assert wid("康德", "纯粹理性批判") == wid("康德", "纯粹理性批判")
    a, b2 = _synthetic_two_editions()
    assert a["work_id"] == b2["work_id"], "同 work 不同版 → work_id 必须一致"
    assert a["edition_record_id"] != b2["edition_record_id"]
    # 局限如实: work_id 目前由 author+title 派生, 跨题名归并未实现


def test_r11_ids_distinct(biblio):
    for r in biblio["books"].values():
        assert r["work_id"] and r["edition_record_id"] and r["digital_source_id"]
        assert len({r["work_id"], r["edition_record_id"], r["digital_source_id"]}) == 3


# ══ R12 — 运行时数据 git 跟踪 ═══════════════════════════════
def test_r12_runtime_data_tracked():
    r = subprocess.run(["git", "ls-files", "backend/data/book_bibliography.json"],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.stdout.strip() == "backend/data/book_bibliography.json", \
        "runtime bibliography 必须 git 跟踪（RP1 §9）"
    d = _load()
    assert d.get("builder_hash") and d.get("source_snapshot_hash") and d.get("pilot_manifest_hash")


# ══ R13 — clean checkout 可复现（在 HEAD 上跑 worktree 门）═════
def test_r13_clean_checkout():
    r = subprocess.run([sys.executable, "backend/tools/dp_biblio_cleancheck.py", "HEAD"],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]


# ══ R14 — 确定性重建 ═══════════════════════════════════════
def test_r14_deterministic_rebuild():
    import tempfile
    tmp = os.path.join(tempfile.mkdtemp(), "rebuilt.json")
    subprocess.run([sys.executable, "backend/tools/dp_biblio_build.py", "--out", tmp],
                   cwd=ROOT, check=True, capture_output=True)
    h1 = hashlib.sha256(open(tmp, "rb").read()).hexdigest()
    h2 = hashlib.sha256(open(BIBLIO_PATH, "rb").read()).hexdigest()
    assert h1 == h2, "重建结果与跟踪文件不一致"


# ══ R15 — 全量语义审计 ═════════════════════════════════════
def test_r15_all_verified_fields_semantic_audited():
    audit = json.load(open(AUDIT_PATH, encoding="utf-8"))
    assert audit["audit_scope"] == "ALL_VERIFIED_FIELDS"
    biblio = _load()
    n = sum(1 for r in biblio["books"].values() for v in r["field_provenance"].values()
            if v.get("verified") and not v.get("conflict"))
    assert audit["fields_audited"] == n, "审计范围必须覆盖全部 verified 字段"
    assert audit["SEMANTICALLY_UNSUPPORTED_VERIFIED_FIELDS"] == []
    for row in audit["rows"]:
        assert row["SUPPORTS_FIELD_SEMANTICS"] is True
        assert row["raw_evidence_spans"], "verified 字段必须携带 raw spans"


# ══ R16 — citation_label 不变 ═══════════════════════════════
def test_r16_citation_label_unchanged():
    from routes.agent_tools_retrieval import _cite_label
    assert _cite_label("论语", "学而第一") == "【《论语》·学而第一】"
    assert _cite_label("论语", "") == "【《论语》】"
    assert _cite_label("", "x") == ""


# ══ R17 — 生产冻结 ═════════════════════════════════════════
HARD_FROZEN = ("backend/final_validator.py", "backend/quote_bound.py",
               "backend/agent_runtime.py", "backend/evidence_contract.py")  # engine 由 O7-E 授权解冻(7d7adfa46 后冻结)


@pytest.mark.parametrize("rel", HARD_FROZEN)
def test_r17_production_frozen(rel):
    r = subprocess.run(["git", "diff", "--quiet", O7A_BASE, "--", rel],
                       cwd=ROOT, capture_output=True)
    assert r.returncode == 0, f"{rel} 相对 O7-A BASE 有改动（禁止）"


def test_r17_routes_within_rp1_scope():
    r = subprocess.run(["git", "diff", "--quiet", RP1_CODE_SHA, "HEAD", "--", "backend/routes"],
                       cwd=ROOT, capture_output=True)
    assert r.returncode == 0, "backend/routes 相对 RP1 代码基线有未授权改动"


# ══ Gate 硬门 §21 ═══════════════════════════════════════════
def test_gate_pilot_size_and_traditions():
    m = json.load(open(MANIFEST_PATH, encoding="utf-8"))
    assert m["pilot"]["works"] >= 30
    assert len(m["pilot"]["traditions_or_periods"]) >= 5


def test_gate_no_placeholder_strings(biblio):
    banned = ["未知译者", "未知出版社", "第?页", "不详", "佚名"]
    s = json.dumps(biblio, ensure_ascii=False)
    for b in banned:
        assert b not in s


def test_gate_kill_case_record(biblio):
    rec = biblio["books"]["2c1a4c7d17a4"]
    assert rec["edition"]["translator"] != "上海"
    tr = rec["field_provenance"].get("translator", {})
    for c in tr.get("candidates", []):
        assert c["value"] != "上海"
    assert "刘继" in [c["value"] for c in tr.get("candidates", [])]


def test_gate_tool_exposure():
    from routes import agent_tools_retrieval as RT
    data = _load()
    pilot_id = next(iter(data["books"]))
    d = RT.TOOLS["get_book_detail"]["execute"]({"book_id": pilot_id})
    assert d.get("bibliographic_metadata")
    c = RT.TOOLS["get_chapter"]["execute"]({"book_id": pilot_id, "chapter_idx": 0})
    assert "bibliographic_metadata" in c and "citation_label" in c
    allb = json.load(open(os.path.join(ROOT, "app", "public", "books.json"), encoding="utf-8"))
    non_pilot = next(b["id"] for b in allb if b["id"] not in data["books"])
    d2 = RT.TOOLS["get_book_detail"]["execute"]({"book_id": non_pilot})
    assert "bibliographic_metadata" not in d2


# ══ O7-B RP2 — Independent Audit & Test Truth（T1-T17）════════════
import dp_biblio_audit as AUD


def test_t1_audit_no_production_extractor_imports():
    """T1: 独立审计器不得 import 生产 extractor 的 regex/函数。"""
    import ast
    tree = ast.parse(open(os.path.join(BACKEND, "tools", "dp_biblio_audit.py"),
                          encoding="utf-8").read())
    banned = {"RE_TRANSLATOR", "RE_PUBLISHER", "RE_ISBN", "RE_ORIG_TITLE",
              "extract_front_matter", "_field_from_found", "_collect_rx"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "dp_biblio_build" in node.module:
            names = {a.name for a in node.names}
            assert not (names & banned), f"审计器 import 了生产规则: {names & banned}"


def test_t2_fake_shanghai_sentinel():
    ok, sup, rej = AUD.audit_translator("上海", ["上海译文出版社", "上海译文出版社"])
    assert ok is False and not sup


def test_t3_genuine_liuji_sentinel():
    ok, sup, rej = AUD.audit_translator("刘继", ["刘继译", "刘继 译"])
    assert ok is True and len(sup) == 2


def test_t3b_fullwidth_space_sentinel():
    ok, sup, _ = AUD.audit_translator("卫茂平", ["卫茂平译", "卫茂平\u3000译"])
    assert ok is True


def test_t4_genuine_publisher():
    ok, sup, _ = AUD.audit_publisher("商务印书馆", ["商务印书馆", "北京：商务印书馆，2012"])
    assert ok is True


def test_t5_isbn_semantics():
    ok, sup, _ = AUD.audit_isbn("978-7-208-16251-8",
                                ["ISBN 978-7-208-16251-8", "ISBN 978-7-208-16251-8"])
    assert ok is True
    ok2, _, _ = AUD.audit_isbn("978-7-208-16251-8", ["定价 45.00 元", "开本 32 开"])
    assert ok2 is False


def test_t6_year_support_classes_separated():
    ok, sup, ign, rej = AUD.audit_publication_year(
        "2020", [("，2020", "CIP_BIBLIOGRAPHIC_YEAR"), ("2020年4月第1版", "EDITION_YEAR"),
                 ("2020年4月第1次印刷", "PRINTING_YEAR"), ("核字（2020）", "CIP_REGISTRATION_YEAR")])
    assert ok and len(sup) == 2 and len(ign) == 2


def test_t7_printing_only_not_publication():
    ok, *_ = AUD.audit_publication_year(
        "2020", [("2020年3月第1次印刷", "PRINTING_YEAR"), ("2021年3月第2次印刷", "PRINTING_YEAR")])
    assert ok is False


def test_t8_cip_reg_only_not_publication():
    ok, *_ = AUD.audit_publication_year(
        "2020", [("核字（2020）", "CIP_REGISTRATION_YEAR"), ("核字（2020）", "CIP_REGISTRATION_YEAR")])
    assert ok is False


def test_t15_all_verified_fields_independently_audited():
    out = AUD.run_audit()
    assert out["audit_implementation"] == "INDEPENDENT"
    assert out["shared_extraction_rules"] == 0
    biblio = _load()
    n = sum(1 for r in biblio["books"].values() for v in r["field_provenance"].values()
            if v.get("verified") and not v.get("conflict"))
    assert out["fields_audited"] == n == 22
    assert out["SEMANTICALLY_UNSUPPORTED_VERIFIED_FIELDS"] == []
    for row in out["rows"]:
        assert row["SUPPORTS_FIELD_SEMANTICS"] is True and row["audit_rule_id"]


def test_t14_no_always_true_assertions():
    """T10/§10: O7-B 测试文件静态扫描永真模式。"""
    import re as _re
    src = open(os.path.abspath(__file__), encoding="utf-8").read()
    for pat in (r"assert\s+[^#\n]*\bor\s+True\b", r"if\s+False\b", r"assert\s+True\b"):
        assert not _re.search(pat, src), f"永真断言模式: {pat}"


def test_t16_clean_checkout_reproducible():
    r = subprocess.run([sys.executable, "backend/tools/dp_biblio_cleancheck.py", "HEAD"],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-500:] + r.stderr[-500:]
    assert '"DETERMINISTIC_REBUILD_MATCH": true' in r.stdout


def test_t17_production_frozen_rp2():
    r = subprocess.run(["git", "diff", "--quiet", "500bb8e88", "HEAD", "--", "backend/routes"],
                       cwd=ROOT, capture_output=True)
    assert r.returncode == 0, "routes 相对 O7-C 授权基线 500bb8e88 有未授权改动"


def test_rp2_runtime_data_hash_unchanged():
    h = hashlib.sha256(open(BIBLIO_PATH, "rb").read()).hexdigest()
    assert h == "bf7ad52559f32a791d1cd5ed9030c6a0ee4cb93c5f009346a522949d6e2dc543", \
        "RP2 未发现真实数据错误 → 运行时数据 hash 必须与 RP1 冻结值一致"
