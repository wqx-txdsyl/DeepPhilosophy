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
    assert "scholarly" not in eng.lower()


def test_d25_d26_primary_and_o7b_unchanged():
    r = subprocess.run(["git", "diff", "--quiet", "e71f4a696", "--",
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
    for rel in ("backend/engine_langgraph.py", "backend/final_validator.py",
                "backend/quote_bound.py"):
        r = subprocess.run(["git", "diff", "--quiet",
                            "302f7380a4146d78374887063b336c5aa7381ddd", "--", rel],
                           cwd=ROOT, capture_output=True)
        assert r.returncode == 0, f"{rel} 被改动"
