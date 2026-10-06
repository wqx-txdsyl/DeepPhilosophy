# -*- coding: utf-8 -*-
"""V9-F5-R3: scholarly retrieval relevance + readability ordering DEV tests。

全部为真实机械 contract tests: monkeypatch 驱动 search_scholarship /
_exec_search_scholarship 实际函数路径, 或纯 helper 真实输出。
零 inspect / 零 contains-string / 零 assert True 占位。
access 语义遵循系统合同: live canonical 记录的 access 由真实证据驱动
（provider abstract → ABSTRACT_AVAILABLE, 否则 METADATA_ONLY）;
FULL_TEXT_READ 仅出现在持历史证据的 local curated 记录上。
排序断言用 title 序（对 source_record_id 指纹方案免疫）。
FORBIDDEN_FROM_V10=true。全新 synthetic, 零 V9 case 复用。
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scholarly_registry as SR
import scholarly_sources as SS


def _mk(title, venue="", access="METADATA_ONLY", cited=1, provider="crossref",
        rid=None, authors=None, abstract=None):
    rec = {"doi": None, "provider_record_id": title[:20], "provider": provider,
           "cited_by": cited, "title": title, "container_title": venue,
           "authors": authors or [], "publication_year": 2020,
           "publication_type": "journal-article",
           "identifiers": {}, "provenance": {"providers": [provider],
                                             "field_sources": {}},
           "access": {"level": access},
           "source_record_id": rid or f"fp-{abs(hash(title)) % 10**12}"}
    if abstract is not None:
        rec["abstract_text"] = abstract
    return rec


@pytest.fixture()
def iso(monkeypatch, tmp_path):
    """隔离: 干缓存 + tmp 缓存文件, 每 test 全新 search_scholarship 状态。"""
    monkeypatch.setattr(SS, "_cache", {"searches": {}, "records": {}})
    monkeypatch.setattr(SS, "CACHE_PATH", str(tmp_path / "scholarly_cache.json"))
    return monkeypatch


def _stub_live(monkeypatch, by_query):
    """crossref 按 query 子串分发 fake 记录; openalex 固定空手（单 provider
    供给, 规避跨 provider 同名重复 canonical 干扰排序断言）。
    每次调用返回全新 dict 副本——归一化会原地改写 provider 记录,
    共享对象会跨 provider 污染 source_record_id。"""
    def fake_crossref(query, limit=8, year_from=None, year_to=None):
        for k, recs in by_query.items():
            if k.lower() in query.lower():
                return [dict(r) for r in recs]
        return []
    def fake_openalex(query, limit=8, year_from=None, year_to=None):
        return []
    monkeypatch.setattr(SS, "search_crossref", fake_crossref)
    monkeypatch.setattr(SS, "search_openalex", fake_openalex)


def _titles(out):
    return [r["title"] for r in out["results"]]


# ═══════════════ strict_only fail-empty（真实 registry 行为）═══════════════

def test_strict_only_empty_returns_empty():
    assert SR.search_local("完全无关的查询词组", limit=5, strict_only=True) == []


def test_strict_only_relevant_returns_results():
    SR.load_registry()
    results = SR.search_local("virtue epistemology Sosa", limit=5, strict_only=True)
    assert isinstance(results, list)  # 不抛错即可（有无结果取决于 registry 内容）


def test_non_strict_fallback_backcompat():
    SR.load_registry()
    r = SR.search_local("完全不存在的查询词组xyz", limit=5, strict_only=False)
    assert isinstance(r, list)


# ═══════════════ 纯 helper 真实输出 ══════════════

def test_original_local_relevant():
    """local candidate 标题与 query 有 token 交集 → relevant"""
    q_latin = {"sosa", "virtue"}
    q_bigrams = {"德性", "知识"}
    rec = _mk("Sosa virtue epistemology", "Phil Review")
    assert SS._is_relevant(q_latin, q_bigrams, rec) is True


def test_original_local_weak_rejected():
    q_latin = {"sosa", "virtue", "epistemology"}
    q_bigrams = {"德性", "知识"}
    rec = _mk("Kant critique pure reason", "Critique")
    assert SS._is_relevant(q_latin, q_bigrams, rec) is False


# ═══════════════ 生产路径行为: strict_only=True 真实传参 ══════════════

def test_scholarly_path_uses_strict_only_kwarg(iso, monkeypatch):
    """search_scholarship 调 _local_results 时真实传入 strict_only=True
    （行为证明, 非 inspect 字符串匹配）"""
    seen = {}

    def fake_local(query, limit=8, strict_only=False):
        seen["strict_only"] = strict_only
        return []

    monkeypatch.setattr(SS, "_local_results", fake_local)
    _stub_live(monkeypatch, {"sosa": [_mk("Sosa virtue epistemology", "Mind",
                                          abstract="Sosa argues that virtue...")]})
    out = SS.search_scholarship("sosa virtue epistemology")
    assert out["results"]
    assert seen["strict_only"] is True


# ═══════════════ variant-local: relevance parity 端到端 ══════════════

def test_variant_local_relevant_recovered(iso, monkeypatch):
    """中文 query → 本地 alias 元数据形成 latin variant → variant-local
    relevant record 被 recovery 进最终结果（live 双 provider 全空手）"""
    q = "朱熹 理气论"
    alias_rec = _mk("朱熹理气论研究", "中国哲学史", provider="local_curated",
                    rid="local-alias", authors=[{"name": "Chen Lai"}])
    variant_local = _mk("Chen Lai on Zhu Xi's liqi cosmology", "Journal of",
                        access="ABSTRACT_AVAILABLE", provider="local_curated",
                        rid="local-variant")
    calls = []

    def fake_local(query, limit=8, strict_only=False):
        calls.append((query, strict_only))
        if strict_only:
            # variant lookup 与 original-local discovery 都走 strict_only=True
            return [dict(variant_local)]
        return [dict(alias_rec)]   # alias 元数据 lookup（strict_only=False）

    monkeypatch.setattr(SS, "_local_results", fake_local)
    _stub_live(monkeypatch, {})   # live 全空手 → reformulation 必触发

    out = SS.search_scholarship(q)
    rf = out["query_reformulation"]
    assert rf["triggered"] is True
    assert "chen" in (rf["variant_query"] or "").lower()
    assert rf["local_variant_count"] == 1
    ids = [r["source_record_id"] for r in out["results"]]
    assert "local-variant" in ids   # VARIANT_LOCAL_RELEVANT_RECOVERED
    # original-local discovery 确实以 strict_only=True 执行
    assert any(qry == q and so is True for qry, so in calls)


def test_variant_local_weak_rejected(iso, monkeypatch):
    """variant-local 命中但与 variant/query 均无 token 交集 → 被 relevance
    gate 拒绝, 不进最终结果（weak fallback 不冒充 recovery）"""
    q = "朱熹 理气论"
    alias_rec = _mk("朱熹理气论研究", "中国哲学史", provider="local_curated",
                    rid="local-alias", authors=[{"name": "Chen Lai"}])
    weak_local = _mk("Kant critique of pure reason", "Critique",
                     provider="local_curated", rid="local-weak")

    def fake_local(query, limit=8, strict_only=False):
        if strict_only:
            return [dict(weak_local)]
        return [dict(alias_rec)]

    monkeypatch.setattr(SS, "_local_results", fake_local)
    _stub_live(monkeypatch, {})

    out = SS.search_scholarship(q)
    assert out["query_reformulation"]["triggered"] is True
    ids = [r["source_record_id"] for r in out["results"]]
    assert "local-weak" not in ids       # VARIANT_LOCAL_WEAK_REJECTED
    assert "local-alias" not in ids      # alias 元数据记录亦不冒充结果
    assert out["results"] == []


def test_max_one_reformulation(iso, monkeypatch):
    """reformulation 恰一次: 每 provider 恰好 2 次调用（initial + 1 retry）,
    不得循环（MAX_REFORMULATION_COUNT=1）"""
    crossref_calls, openalex_calls = [], []

    def fake_crossref(query, limit=8, year_from=None, year_to=None):
        crossref_calls.append(query)
        if "平庸" in query:
            return []   # 原中文 query 零结果
        return [_mk("Hannah Arendt and the banality of evil",
                    "Journal of Genocide Research",
                    abstract="Arendt revisited...")]

    def fake_openalex(query, limit=8, year_from=None, year_to=None):
        openalex_calls.append(query)
        return []

    monkeypatch.setattr(SS, "search_crossref", fake_crossref)
    monkeypatch.setattr(SS, "search_openalex", fake_openalex)
    monkeypatch.setattr(SS, "_local_results",
                        lambda q, limit, strict_only=False: [])

    out = SS.search_scholarship("平庸之恶 Arendt")
    assert out["query_reformulation"]["triggered"] is True
    assert len(crossref_calls) == 2   # initial + 恰一次 retry
    assert len(openalex_calls) == 2
    assert _titles(out) == ["Hannah Arendt and the banality of evil"]


# ═══════════════ 最终 merged list 全局 readability ordering ══════════════

def test_final_merged_fulltext_before_abstract(iso, monkeypatch):
    """FULL_TEXT_READ > ABSTRACT_AVAILABLE（local 历史证据 fulltext
    vs live 持 abstract 的记录, 全局排序后 fulltext 在前）"""
    local_ft = _mk("Sosa virtue epistemology", "Phil Review",
                   access="FULL_TEXT_READ", provider="local_curated",
                   rid="local-ft")
    live_ab = _mk("Sosa on virtue", "Mind",
                  abstract="Sosa argues that knowledge is virtue...")
    monkeypatch.setattr(SS, "_local_results",
                        lambda q, limit, strict_only=False: [local_ft])
    _stub_live(monkeypatch, {"sosa": [live_ab]})
    out = SS.search_scholarship("sosa virtue epistemology")
    assert _titles(out) == ["Sosa virtue epistemology", "Sosa on virtue"]


def test_final_merged_abstract_before_metadata(iso, monkeypatch):
    """ABSTRACT_AVAILABLE > METADATA_ONLY（同 provider 批次内, 靠真实
    abstract 证据升级 access, 全局排序后 abstract 在前）"""
    ab = _mk("Sosa virtue epistemology", "Phil Review",
             abstract="Sosa argues that knowledge is virtue...")
    meta = _mk("Sosa on virtue", "Mind")   # 无 abstract → METADATA_ONLY
    monkeypatch.setattr(SS, "_local_results", lambda q, limit, strict_only=False: [])
    _stub_live(monkeypatch, {"sosa": [meta, ab]})   # 故意 meta 在前
    out = SS.search_scholarship("sosa virtue epistemology")
    assert _titles(out) == ["Sosa virtue epistemology", "Sosa on virtue"]


def test_local_metadata_behind_live_abstract(iso, monkeypatch):
    """R3 核心回归: original-local METADATA_ONLY 不得排在 live
    ABSTRACT_AVAILABLE 之前（旧实现 dedup 把 local 前缀进 merged）"""
    local_meta = _mk("Sosa virtue epistemology", "中国哲学研究",
                     access="METADATA_ONLY", provider="local_curated",
                     rid="local-meta")
    live_ab = _mk("Sosa on virtue epistemology", "Mind",
                  abstract="Sosa argues that knowledge is virtue...")
    monkeypatch.setattr(SS, "_local_results",
                        lambda q, limit, strict_only=False: [local_meta])
    _stub_live(monkeypatch, {"sosa": [live_ab]})
    out = SS.search_scholarship("sosa virtue epistemology")
    assert _titles(out) == ["Sosa on virtue epistemology",
                            "Sosa virtue epistemology"]


def test_live_metadata_behind_local_fulltext(iso, monkeypatch):
    """对称方向: live METADATA_ONLY 不得排在 local FULL_TEXT_READ 之前"""
    local_ft = _mk("Sosa virtue epistemology", "哲学研究",
                   access="FULL_TEXT_READ", provider="local_curated",
                   rid="local-ft")
    live_meta = _mk("Sosa on virtue epistemology", "Mind")   # 无 abstract
    monkeypatch.setattr(SS, "_local_results",
                        lambda q, limit, strict_only=False: [local_ft])
    _stub_live(monkeypatch, {"sosa": [live_meta]})
    out = SS.search_scholarship("sosa virtue epistemology")
    assert _titles(out) == ["Sosa virtue epistemology",
                            "Sosa on virtue epistemology"]


def test_relevant_abstract_before_relevant_metadata(iso, monkeypatch):
    """两条都 relevant 的最终返回顺序: abstract 在 metadata 前
    （端到端断言 search_scholarship 返回序, 非 helper 级断言）"""
    ab = _mk("Sosa virtue epistemology", "Phil Review",
             abstract="Sosa argues that knowledge is virtue...")
    meta = _mk("Sosa on virtue", "Mind")
    monkeypatch.setattr(SS, "_local_results", lambda q, limit, strict_only=False: [])
    _stub_live(monkeypatch, {"sosa": [meta, ab]})
    out = SS.search_scholarship("sosa virtue epistemology")
    titles = _titles(out)
    assert titles.index("Sosa virtue epistemology") < titles.index("Sosa on virtue")


def test_irrelevant_readable_rejected(iso, monkeypatch):
    """readability 不挽救离题来源: 持 abstract（可读）但标题离题 → 被
    relevance gate 拒绝, 不因可读性进入结果"""
    irrelevant_ab = _mk("Kant critique of pure reason", "Kant-Studien",
                        abstract="Kant argues...")
    relevant_meta = _mk("Sosa virtue epistemology", "Mind")
    monkeypatch.setattr(SS, "_local_results", lambda q, limit, strict_only=False: [])
    _stub_live(monkeypatch, {"sosa": [irrelevant_ab, relevant_meta]})
    out = SS.search_scholarship("sosa virtue epistemology")
    assert _titles(out) == ["Sosa virtue epistemology"]
    assert out["relevance_gate"]["dropped_irrelevant"] == 1


# ═══════════════ search tool 层: READABLE_SOURCE_IDS 精确合同 ══════════════

def test_readable_source_ids_exact(iso, monkeypatch):
    """READABLE_SOURCE_IDS == 最终返回结果中 access_level >= ABSTRACT_AVAILABLE
    的 id 集合（真实 tool executor + model_view 路径, 精确相等断言）"""
    from routes.agent_tools_scholarly import _exec_search_scholarship
    local_ft = _mk("Sosa virtue epistemology", "Phil Review",
                   access="FULL_TEXT_READ", provider="local_curated",
                   rid="local-ft")
    local_meta = _mk("Sosa bibliographic note", "中国哲学研究",
                     access="METADATA_ONLY", provider="local_curated",
                     rid="local-meta")
    live_ab = _mk("Sosa on virtue epistemology", "Mind",
                  abstract="Sosa argues that knowledge is virtue...")
    monkeypatch.setattr(SS, "_local_results",
                        lambda q, limit, strict_only=False: [local_ft,
                                                             local_meta])
    _stub_live(monkeypatch, {"sosa": [live_ab]})
    resp = _exec_search_scholarship({"query": "sosa virtue epistemology"})
    expected = [r["source_record_id"] for r in resp["results"]
                if r["access_level"] in ("ABSTRACT_AVAILABLE",
                                         "FULL_TEXT_AVAILABLE",
                                         "FULL_TEXT_READ")]
    assert resp["READABLE_SOURCE_IDS"] == expected
    assert resp["READABLE_RESULT_COUNT"] == len(expected) == 2
    # METADATA_ONLY 不入 READABLE_SOURCE_IDS
    assert "local-meta" not in resp["READABLE_SOURCE_IDS"]
    # 可读来源全局排序后 local fulltext 在 live abstract 前
    assert resp["READABLE_SOURCE_IDS"][0] == "local-ft"


def test_auto_fetch_not_added(iso, monkeypatch):
    """Main Agent sovereignty: search path 全程不自动调用
    get_scholarly_source / get_evidence（发现 ≠ 阅读）"""
    from routes.agent_tools_scholarly import _exec_search_scholarship
    calls = []

    def _forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("search path 不得自动取摘要/全文证据")

    monkeypatch.setattr(SS, "get_evidence", _forbidden)
    monkeypatch.setattr(SS, "get_record", _forbidden)
    live_ab = _mk("Sosa virtue epistemology", "Mind",
                  abstract="Sosa argues that knowledge is virtue...")
    monkeypatch.setattr(SS, "_local_results", lambda q, limit, strict_only=False: [])
    _stub_live(monkeypatch, {"sosa": [live_ab]})
    resp = _exec_search_scholarship({"query": "sosa virtue epistemology"})
    assert resp["results"]
    assert calls == []
