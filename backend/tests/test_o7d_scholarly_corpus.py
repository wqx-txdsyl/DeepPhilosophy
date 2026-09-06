# -*- coding: utf-8 -*-
"""O7-D Scholarly Corpus tests（D2-D30; D1 在 o7c 套件）。

锁死: registry 完整性/确定性重建/版权边界/离线语义/local-live 去重/
历史读≠当前读/无隐藏认知组件/生产冻结。
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

import scholarly_registry as SR
import scholarly_sources as SS

REG_DIR = os.path.join(BACKEND, "data", "scholarly")


@pytest.fixture(scope="module")
def reg():
    return SR.load_registry()


def test_d2_registry_ids_unique(reg):
    ids = [r["source_record_id"] for r in reg.values()]
    assert len(ids) == len(set(ids))


def test_d3_registry_doi_dedup(reg):
    dois = [r["identifiers"]["doi"] for r in reg.values() if r["identifiers"].get("doi")]
    assert len(dois) == len(set(dois))


def test_d4_local_live_same_doi_merges(monkeypatch):
    local = {"source_record_id": "doi:10.1/x", "identifiers": {"doi": "10.1/x"},
             "title": "A", "provider_records": [], "provenance": {"providers": ["LOCAL_CURATED"]}}
    live = {"source_record_id": "doi:10.1/x", "identifiers": {"doi": "10.1/x"},
            "title": "A", "provider_records": [], "provenance": {"providers": ["crossref"]}}
    merged = SS._dedup_local_live([local], [live])
    assert len(merged) == 1


def test_d5_cache_not_registry():
    # runtime cache 与 curated registry 是不同文件、不同生命周期
    registry_path = os.path.join(REG_DIR, "registry.jsonl")
    assert os.path.exists(registry_path)
    cache = os.path.join(BACKEND, "data", "scholarly_cache.json")
    assert cache != registry_path


def test_d6_registry_deterministic_rebuild():
    before = json.load(open(os.path.join(REG_DIR, "corpus_manifest.json"), encoding="utf-8"))
    r = subprocess.run([sys.executable, "backend/tools/dp_o7d_registry.py"],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-400:]
    after = json.load(open(os.path.join(REG_DIR, "corpus_manifest.json"), encoding="utf-8"))
    assert before["registry_sha256"] == after["registry_sha256"], "重建漂移"
    assert before["evidence_sha256"] == after["evidence_sha256"]


def test_d7_discovery_snapshot_frozen():
    snap = json.load(open(os.path.join(ROOT, "docs/evidence",
                                       "PHIAGENT_O7D_DISCOVERY_SNAPSHOT.json"),
                          encoding="utf-8"))
    h = snap["discovery_snapshot_hash"]
    snap2 = dict(snap)
    snap2.pop("discovery_snapshot_hash")
    blob = json.dumps(snap2, ensure_ascii=False, sort_keys=True).encode()
    assert hashlib.sha256(blob).hexdigest() == h, "snapshot 与其 hash 不一致"


def test_d8_metadata_only_no_invented_content(reg):
    ev = SR._load_jsonl(os.path.join(REG_DIR, "evidence.jsonl"))
    ev_by_sid = {}
    for e in ev:
        ev_by_sid.setdefault(e["source_record_id"], []).append(e)
    for sid, r in reg.items():
        if r["ingest"]["access_level_at_ingest"] == "METADATA_ONLY":
            assert not ev_by_sid.get(sid), f"{sid} METADATA_ONLY 却有持久内容"


def test_d9_abstract_provenance_retained():
    ev = SR._load_jsonl(os.path.join(REG_DIR, "evidence.jsonl"))
    for e in ev:
        if e["evidence_type"] == "ABSTRACT":
            assert e.get("abstract_source") and e.get("abstract_hash")
            assert e.get("evidence_origin") == "ABSTRACT_METADATA"


def test_d10_fulltext_evidence_requires_verified_read():
    ev = SR._load_jsonl(os.path.join(REG_DIR, "evidence.jsonl"))
    for e in ev:
        if e["evidence_type"] == "FULLTEXT_PASSAGE":
            assert e["access_level_at_ingest"] == "FULL_TEXT_READ"
            assert e.get("content_hash") and e.get("verified_document_kind") == "PDF"
            assert e.get("parser") == "pdftotext"
            assert e.get("evidence_origin") == "PERSISTED_VERIFIED_READ"
            assert len(e["text"]) <= 1200


def test_d11_no_pdf_or_body_committed():
    for f in os.listdir(REG_DIR):
        p = os.path.join(REG_DIR, f)
        assert not f.lower().endswith((".pdf", ".bin", ".doc", ".epub"))
        if f.endswith(".jsonl"):
            for line in open(p, encoding="utf-8"):
                item = json.loads(line)
                for key, v in item.items():
                    if isinstance(v, str) and key == "text":
                        assert len(v) <= 3600, "证据文本超长（疑似全文持久化）"


def test_d12_reuse_unknown_when_licence_unknown(reg):
    for r in reg.values():
        assert r.get("reuse_status") in ("UNKNOWN", "METADATA_ONLY",
                                         "ACCESSIBLE_BUT_REUSE_UNVERIFIED")
        if r["reuse_status"] == "UNKNOWN":
            assert r.get("license_verified") is False and not r.get("license")


def test_d13_local_only_offline(monkeypatch):
    def boom(*a, **k):
        raise SS.ProviderError("PROVIDER_UNAVAILABLE", "network down")
    monkeypatch.setattr(SS, "search_crossref", boom)
    monkeypatch.setattr(SS, "search_openalex", boom)
    monkeypatch.setattr(SS, "_cache", {"searches": {}, "records": {}})
    out = SS.search_scholarship("kant thing in itself", limit=5)
    assert out["results"], "离线时本地 registry 应可返回"
    assert out.get("offline_mode") is True
    # D15: 本地结果不冒充实时检索
    assert "本地学术 registry" in out.get("note", "") and "非实时检索" in out["note"]
    # D14: 外部失败如实报告
    assert out["errors"] and all(e["error"] == "PROVIDER_UNAVAILABLE" for e in out["errors"])


def test_d16_no_local_live_duplicates_in_top5():
    # 构造: local 与 live 各 2 条, 其中 1 条同 DOI → 合并后 3 条
    mk = lambda sid, doi, prov: {"source_record_id": sid,
                                 "identifiers": {"doi": doi},
                                 "provider_records": [],
                                 "provenance": {"providers": [prov]}}
    local = [mk("doi:10.1/a", "10.1/a", "LOCAL_CURATED"),
             mk("openalex:W1", None, "LOCAL_CURATED")]
    live = [mk("doi:10.1/a", "10.1/a", "crossref"),
            mk("doi:10.1/b", "10.1/b", "crossref")]
    merged = SS._dedup_local_live(local, live)
    assert len(merged) == 3 and len({r["source_record_id"] for r in merged}) == 3


def test_d17_d18_historical_read_evidence():
    # 合成: registry 中一条 FULL_TEXT_READ 历史记录 + passages
    reg = SR.load_registry()
    synthetic = {"source_record_id": "doi:10.1/hist", "title": "Hist",
                 "identifiers": {"doi": "10.1/hist"}, "provider_records": [],
                 "provenance": {"providers": ["crossref"]}, "conflicts": [],
                 "cluster_ids_accepted": ["syn"], "cluster_ids_discovery_only": [],
                 "ingest": {"access_level_at_ingest": "FULL_TEXT_READ"},
                 "reuse_status": "ACCESSIBLE_BUT_REUSE_UNVERIFIED",
                 "abstract": {"text": None}}
    ev = [{"source_record_id": "doi:10.1/hist", "evidence_id": "ev-syn",
           "evidence_type": "FULLTEXT_PASSAGE", "text": "p " * 100,
           "access_level_at_ingest": "FULL_TEXT_READ",
           "evidence_origin": "PERSISTED_VERIFIED_READ",
           "content_hash": "h", "page": None, "locator": None}]
    reg["doi:10.1/hist"] = synthetic
    SR._evidence["doi:10.1/hist"] = ev
    assert SR.evidence_for("doi:10.1/hist")[0]["evidence_origin"] == "PERSISTED_VERIFIED_READ"
    # D18: 历史(持久化验证读) ≠ 当前实时读
    assert SR.evidence_for("doi:10.1/hist")[0]["evidence_origin"] != "LIVE_CURRENT_READ"
    del reg["doi:10.1/hist"]; del SR._evidence["doi:10.1/hist"]


def test_d19_d20_locator_honesty():
    ev = SR._load_jsonl(os.path.join(REG_DIR, "evidence.jsonl"))
    for e in ev:
        assert e.get("page") is None and e.get("locator") is None or \
               e["evidence_type"] == "FULLTEXT_PASSAGE" and e.get("locator") in (None, "PDF_PAGE")
    reg = SR.load_registry()
    for r in reg.values():
        assert "canonical_locator" not in r and "interpretation" not in r


def test_d21_no_proposition_db(reg):
    banned = ("supports_interpretation", "opposes", "stance", "position_on",
              "scholar_view")
    for r in reg.values():
        for b in banned:
            assert b not in r


def test_d22_d23_no_hidden_components():
    import inspect
    for mod in (SS, SR):
        src = inspect.getsource(mod)
        for banned in ("sufficiency", "enough_literature", "两个解释", "two_interpretations"):
            assert banned not in src.lower(), f"{mod.__name__} 含隐藏认知组件: {banned}"
    # D23: 搜索路径无自动刷新（search_local 只读; 无网络调用）
    src = inspect.getsource(SR.search_local)
    assert "urlopen" not in src and "http" not in src.lower()


def test_d24_tool_authorory_unchanged():
    import routes.agent_tools_scholarly as ATS
    scholarly = [n for n in ATS.TOOLS if "scholar" in n]
    assert set(scholarly) == {"search_scholarship", "get_scholarly_source"}
    eng = open(os.path.join(BACKEND, "engine_langgraph.py"), encoding="utf-8").read()
    assert "import scholarly_sources" not in eng and "scholarly_sources." not in eng


def test_d25_d26_primary_and_o7b_unchanged():
    r = subprocess.run(["git", "diff", "--quiet", "e71f4a696", "HEAD", "--",
                        "backend/routes/agent_tools_retrieval.py"],
                       cwd=ROOT, capture_output=True)
    assert r.returncode == 0
    h = hashlib.sha256(open(os.path.join(BACKEND, "data", "book_bibliography.json"),
                            "rb").read()).hexdigest()
    assert h == "bf7ad52559f32a791d1cd5ed9030c6a0ee4cb93c5f009346a522949d6e2dc543"


def test_d28_general_persona_corpus_same():
    # 单一 registry; 无 persona 分叉语料路径
    src = open(os.path.join(BACKEND, "scholarly_registry.py"), encoding="utf-8").read()
    assert "persona" not in src.lower()


def test_d29_model_facing_compact():
    mv = SS.model_view(next(iter(SR.load_registry().values())))
    assert "provider_records" not in mv and "conflicts" not in mv


def test_d30_production_frozen():
    for rel in ("backend/final_validator.py", "backend/quote_bound.py"):
        r = subprocess.run(["git", "diff", "--quiet",
                            "302f7380a4146d78374887063b336c5aa7381ddd", "--", rel],
                           cwd=ROOT, capture_output=True)
        assert r.returncode == 0, f"{rel} 被改动"


# ══ O7-D RP1: Curated-Corpus Truth & Local Evidence Runtime（R1-R19）═══
def _counts(reg):
    cur = [r for r in reg.values() if r["association_status"] == "CURATED"]
    disc = [r for r in reg.values() if r["association_status"] == "DISCOVERY_ONLY"]
    return cur, disc


def test_r1_r2_association_status_correct(reg):
    cur, disc = _counts(reg)
    assert len(cur) == 276 and len(disc) == 34
    for r in cur:
        assert r["cluster_ids_accepted"]
    for r in disc:
        assert not r["cluster_ids_accepted"] and r["cluster_ids_discovery_only"]


def test_r3_default_local_search_excludes_discovery_only(reg):
    for q in ("kant", "nietzsche", "confucius"):
        for r in SR.search_local(q, 10):
            assert r["association_status"] == "CURATED", \
                f"discovery-only {r['source_record_id']} 泄入默认本地搜索"


def test_r4_cluster_tags_indexed():
    # accepted cluster tag 命中（title/abstract 无该词也该能搜到）
    rows = SR.search_local('"kant-schematism"', 5)
    assert any("kant-schematism" in r["cluster_ids_accepted"] for r in rows), \
        "cluster_ids_accepted 未实际进入 FTS 索引"


def test_r5_nonexistent_cluster_ids_field_unused():
    import inspect
    src = inspect.getsource(SR.build_index)
    assert 'r.get("cluster_ids")' not in src and "cluster_ids_accepted" in src


def test_r6_discovery_only_no_curated_primary_links(reg):
    for r in reg.values():
        if r["association_status"] == "DISCOVERY_ONLY":
            assert not r["related_primary_book_ids"], \
                f"{r['source_record_id']} discovery-only 继承了 curated primary link"


def test_r7_r8_local_origin_and_source_provenance(reg):
    rs = SR.search_local("kant thing in itself", 3)
    assert rs
    for r in rs:
        assert r["retrieval_origin"] == "LOCAL_CURATED"        # R7
        assert "crossref" in r["provenance"]["providers"]       # R8 书目来源保留
        mv = SS.model_view(r)
        assert mv["retrieval_origin"] == "LOCAL_CURATED"
        assert mv["source_providers"] == r["provenance"]["providers"]


def test_r9_offline_not_mislabeled_live(monkeypatch):
    def boom(*a, **k):
        raise SS.ProviderError("PROVIDER_UNAVAILABLE", "down")
    monkeypatch.setattr(SS, "search_crossref", boom)
    monkeypatch.setattr(SS, "search_openalex", boom)
    monkeypatch.setattr(SS, "_cache", {"searches": {}, "records": {}})
    out = SS.search_scholarship("kant thing in itself", limit=5)
    for r in out["results"]:
        mv = SS.model_view(r)
        assert mv["retrieval_origin"] == "LOCAL_CURATED" != mv["source_providers"][0]


def test_r10_dedup_preserves_origin_truth():
    local = {"source_record_id": "doi:10.1/d", "identifiers": {"doi": "10.1/d"},
             "title": "A", "provider_records": [],
             "provenance": {"providers": ["crossref"]},
             "retrieval_origin": "LOCAL_CURATED"}
    live = {"source_record_id": "doi:10.1/d", "identifiers": {"doi": "10.1/d"},
            "title": "A", "provider_records": [],
            "provenance": {"providers": ["crossref"]}}
    merged = SS._dedup_local_live([local], [live])
    assert len(merged) == 1
    assert merged[0]["retrieval_origin"] == "LOCAL_CURATED+LIVE"
    assert merged[0]["provenance"]["providers"] == ["crossref"]


def _inject_persisted_evidence(sid, passages=True, abstract=True):
    reg = SR.load_registry()
    base = {"source_record_id": sid, "title": "Persisted", "identifiers": {"doi": None},
            "provider_records": [], "provenance": {"providers": ["crossref"], "field_sources": {"title": "crossref"}},
            "publication_year": 2000, "publication_type": "JOURNAL_ARTICLE",
            "container_title": "V", "authors": [{"name": "A. Author", "orcid": None}],
            "citation_capability": {}, "stable_urls": [],
            "peer_review_status": "UNVERIFIED",
            "philosophical_role": "UNKNOWN",
            "conflicts": [], "cluster_ids_accepted": ["kant-schematism"],
            "cluster_ids_discovery_only": [], "related_primary_book_ids": [],
            "association_status": "CURATED",
            "ingest": {"access_level_at_ingest":
                       "FULL_TEXT_READ" if passages else "ABSTRACT_AVAILABLE"},
            "reuse_status": "ACCESSIBLE_BUT_REUSE_UNVERIFIED",
            "abstract": {"text": "persisted abstract." if abstract else None,
                         "source": "crossref" if abstract else None,
                         "hash": "h0" if abstract else None},
            "access": {"level": "ABSTRACT_AVAILABLE" if abstract else "METADATA_ONLY",
                       "evidence": "x", "checked_at": 1, "full_text_url": None,
                       "content_hash": None}}
    reg[sid] = base
    ev = []
    if abstract:
        ev.append({"source_record_id": sid, "evidence_id": "ev-abs",
                   "evidence_type": "ABSTRACT", "text": "persisted abstract.",
                   "abstract_source": "crossref", "abstract_hash": "h1",
                   "evidence_origin": "ABSTRACT_METADATA"})
    if passages:
        ev.append({"source_record_id": sid, "evidence_id": "ev-p1",
                   "evidence_type": "FULLTEXT_PASSAGE", "text": "p " * 100,
                   "content_hash": "doc-h", "access_level_at_ingest": "FULL_TEXT_READ",
                   "evidence_origin": "PERSISTED_VERIFIED_READ",
                   "page": None, "locator": None})
    SR._evidence[sid] = ev
    return base


def test_r11_persisted_abstract_tool_path(monkeypatch):
    sid = "doi:10.1/persisted-abs"
    monkeypatch.setattr(SS, "get_record", lambda s: _inject_persisted_evidence(
        s, passages=False, abstract=True))
    from routes import agent_tools_scholarly as ATS
    out = ATS.TOOLS["get_scholarly_source"]["execute"](
        {"source_record_id": sid, "requested_access": "ABSTRACT"})
    assert out.get("abstract", {}).get("text", "").startswith("persisted abstract")
    SR.load_registry().pop(sid, None); SR._evidence.pop(sid, None)


def test_r12_r13_r14_r15_persisted_fulltext_tool_path(monkeypatch):
    sid = "doi:10.1/persisted-ft"
    monkeypatch.setattr(SS, "get_record", lambda s: _inject_persisted_evidence(
        s, passages=True, abstract=True))
    from routes import agent_tools_scholarly as ATS
    out = ATS.TOOLS["get_scholarly_source"]["execute"](
        {"source_record_id": sid, "requested_access": "FULL_TEXT_IF_LEGALLY_AVAILABLE"})
    assert out.get("evidence_passages"), "持久化 passages 未通过工具路径返回"
    assert out.get("evidence_origin") == "PERSISTED_VERIFIED_READ"      # R13
    assert out.get("evidence_origin") != "LIVE_CURRENT_READ"            # R14
    assert out.get("historical_evidence_level") == "FULL_TEXT_READ"
    assert "本轮未重新获取全文" in out["access_notes"]
    # R15: 当前 access 不被历史读虚构
    assert out["access_level_after"] != "FULL_TEXT_READ"
    SR.load_registry().pop(sid, None); SR._evidence.pop(sid, None)


def test_r16_r17_bibliographic_audit_includes_authors():
    src = open(os.path.join(BACKEND, "tools", "evaluation", "o7d_gate.py"),
               encoding="utf-8").read()
    assert '"authors"' in src.split("def phase_b")[1].split("def phase_d")[0]
    g = json.load(open(os.path.join(ROOT, "docs/evidence",
                                    "PHIAGENT_O7D_CORPUS_GATE.json"), encoding="utf-8"))
    b = g["phases"]["B"]
    assert b["sample"] >= 50 and b["fields_per_record"] == 5
    assert b["fields_checked"] >= 250 and b["BIBLIOGRAPHIC_WRONG_FIELDS"] == []


def test_r18_deterministic_rebuild_rp1():
    before = json.load(open(os.path.join(REG_DIR, "corpus_manifest.json"),
                            encoding="utf-8"))
    r = subprocess.run([sys.executable, "backend/tools/dp_o7d_registry.py"],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0
    after = json.load(open(os.path.join(REG_DIR, "corpus_manifest.json"),
                           encoding="utf-8"))
    assert before["registry_sha256"] == after["registry_sha256"]


def test_r19_production_frozen_rp1():
    for rel in ("backend/final_validator.py", "backend/quote_bound.py"):
        r = subprocess.run(["git", "diff", "--quiet",
                            "302f7380a4146d78374887063b336c5aa7381ddd", "--", rel],
                           cwd=ROOT, capture_output=True)
        assert r.returncode == 0


# ══ O7-D Final Micro Patch: Local Provenance Closure（F1-F6）══════
def test_f1_f2_f3_registry_fallback_origin(monkeypatch):
    # F1: cache miss + registry hit → LOCAL_CURATED（不动 registry 持久数据）
    sid = "doi:10.1/mp-origin"
    rec = _inject_persisted_evidence(sid, passages=False, abstract=True)
    monkeypatch.setattr(SS, "_load_cache", lambda: {"searches": {}, "records": {}})
    got = SS.get_record(sid)
    assert got["retrieval_origin"] == "LOCAL_CURATED"          # F1
    mv = SS.model_view(got)
    assert mv["retrieval_origin"] == "LOCAL_CURATED"           # F2
    assert mv["retrieval_origin"] != "LIVE"
    assert mv["source_providers"] == ["crossref"]              # F3
    # registry 持久数据未被污染
    assert "retrieval_origin" not in SR.load_registry()[sid]
    SR.load_registry().pop(sid, None); SR._evidence.pop(sid, None)


def test_f4_persisted_abstract_origin_through_tool(monkeypatch):
    sid = "doi:10.1/mp-abs-origin"
    monkeypatch.setattr(SS, "get_record",
                        lambda s: dict(_inject_persisted_evidence(
                            s, passages=False, abstract=True),
                            retrieval_origin="LOCAL_CURATED"))
    from routes import agent_tools_scholarly as ATS
    out = ATS.TOOLS["get_scholarly_source"]["execute"](
        {"source_record_id": sid, "requested_access": "ABSTRACT"})
    assert out.get("abstract", {}).get("text")
    assert out.get("evidence_origin") == "ABSTRACT_METADATA"   # F4 真行为
    SR.load_registry().pop(sid, None); SR._evidence.pop(sid, None)


def test_f5_f6_persisted_fulltext_unchanged(monkeypatch):
    sid = "doi:10.1/mp-ft-origin"
    monkeypatch.setattr(SS, "get_record",
                        lambda s: dict(_inject_persisted_evidence(
                            s, passages=True, abstract=True),
                            retrieval_origin="LOCAL_CURATED"))
    from routes import agent_tools_scholarly as ATS
    out = ATS.TOOLS["get_scholarly_source"]["execute"](
        {"source_record_id": sid, "requested_access": "FULL_TEXT_IF_LEGALLY_AVAILABLE"})
    assert out.get("evidence_origin") == "PERSISTED_VERIFIED_READ"   # F5
    assert out.get("access_level_after") != "FULL_TEXT_READ"          # F6
    SR.load_registry().pop(sid, None); SR._evidence.pop(sid, None)
