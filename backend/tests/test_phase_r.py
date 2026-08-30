# -*- coding: utf-8 -*-
"""Phase R（2026-08-30）—— Retrieval / Runtime Optimization 回归集

R1  AIAuthor Lazy Bundle: persona/memory/graph/corpus/user_model 按数据域独立懒加载
    （调用 persona 不加载 corpus; 调用 memory 不强制 corpus/graph; 每域独立缓存;
      线程安全; 不改工具 API contract; 无每请求重复 json.load）
R2  Nietzsche Hybrid Retrieval: dense（复用 AIAuthor vector 数据）+ lexical BM25
    → RRF 合并 → rerank（短语/tier 权威）→ top-k echoes; 元数据完整;
    embedding 429 → Phase S 词法降级; 检索失败不拖垮 Agent
R3  Corpus Access: 索引 artifact 按行号 seek 精确取 chunk 原文;
    健康路径不整载语料文本; 不加载 453MB all_chunks.json

UAT（真实 retrieval）在 backend/tools/dp_perf_phase_r.py（含 429 容忍与 baseline 对比）;
本文件为确定性单测（embedding 一律 mock, 不依赖网络）。
"""
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import agents as AGENTS
import philo_retrieval as pr
import routes.agent_core as agent_core


# ── 公共设施 ─────────────────────────────────────────
@pytest.fixture(autouse=True)
def _clean_state():
    """每个用例独立状态: bundle 域缓存 + 检索索引缓存 + embedding 熔断器复位"""
    AGENTS.reset_bundle_cache()
    pr.reset_state()
    with agent_core._EMBED_CIRCUIT_LOCK:
        agent_core._EMBED_CIRCUIT.update({"open": False, "opened_at": 0.0, "reason": ""})
    agent_core._embed_status.update({"mode": "vector", "degraded_reason": ""})
    yield
    AGENTS.reset_bundle_cache()
    pr.reset_state()
    with agent_core._EMBED_CIRCUIT_LOCK:
        agent_core._EMBED_CIRCUIT.update({"open": False, "opened_at": 0.0, "reason": ""})


def _philo(tool):
    return AGENTS.make_philo_tool("nietzsche", tool)


def _mock_dense_at(row):
    """embedding mock: 直接用 row 行的存量向量作 query 向量 → 该行必为 dense top-1
    （不依赖网络; 验证 dense 机制本身）"""
    import numpy as np

    def fake(q):
        return [float(x) for x in np.load(pr.VEC_FILE)[row]]
    return fake


# ═══════════════════════════════════════════════════════
# R1 — Lazy Bundle: 数据域独立加载
# ═══════════════════════════════════════════════════════
def test_r1_persona_tools_load_only_persona():
    for tool, args in [("philosopher_concepts", {"concept": "权力意志"}),
                       ("philosopher_style", {}),
                       ("philosopher_period", {"period": "early"})]:
        AGENTS.reset_bundle_cache()
        r = _philo(tool)(args)
        assert not r.get("error"), f"{tool}: {r.get('error')}"
        assert AGENTS.loaded_domains("nietzsche") == ["persona"], \
            f"{tool} 应只加载 persona 域, 实际 {AGENTS.loaded_domains('nietzsche')}"


def test_r1_memory_does_not_load_corpus_graph():
    r = _philo("philosopher_memory")({"question": "尼采何时患病"})
    assert r.get("memories"), "记忆召回应有结果"
    doms = AGENTS.loaded_domains("nietzsche")
    assert "memory" in doms
    assert "corpus" not in doms and "graph" not in doms, f"memory 调用不得强制 corpus/graph: {doms}"


def test_r1_graph_loaded_only_by_graph_call():
    r = _philo("philosopher_graph")({"concept": "永恒轮回"})
    assert r.get("entities"), "图谱查询应有结果"
    assert AGENTS.loaded_domains("nietzsche") == ["graph"]


def test_r1_user_model_domain_independent():
    r = _philo("philosopher_user")({"question": "超人是不是强者"})
    assert r.get("likely_misconceptions")
    assert AGENTS.loaded_domains("nietzsche") == ["user_model"]


def test_r1_corpus_tool_never_loads_bundle_corpus():
    """philosopher_corpus（索引就绪）不得加载 453MB bundle corpus 域"""
    assert pr.artifacts_available(), "nietzsche 索引 artifact 缺失（先跑 dp_build_nietzsche_index.py）"
    r = _philo("philosopher_corpus")({"query": "权力意志"})
    assert "error" not in r
    assert isinstance(r.get("echoes"), list)
    assert "corpus" not in AGENTS.loaded_domains("nietzsche")


def test_r1_domains_cached_not_reloaded():
    """已加载域复用: 二次调用不重复读盘（文件读取计数）"""
    import builtins
    reads = {"n": 0}
    real_open = builtins.open

    def counting_open(file, *a, **kw):
        if isinstance(file, (str, os.PathLike)) and str(file).endswith("persona_model.json"):
            reads["n"] += 1
        return real_open(file, *a, **kw)

    builtins.open = counting_open
    try:
        _philo("philosopher_concepts")({"concept": "权力意志"})
        _philo("philosopher_concepts")({"concept": "永恒轮回"})
        _philo("philosopher_style")({})
    finally:
        builtins.open = real_open
    assert reads["n"] == 1, f"persona_model.json 应只读盘一次, 实际 {reads['n']} 次"


def test_r1_lazy_view_dict_semantics():
    v = AGENTS.load_bundle("nietzsche")
    assert v.get("nonexistent_key") is None
    assert "corpus" in v                      # __contains__ 不触发加载
    assert AGENTS.loaded_domains("nietzsche") == []
    persona = v.get("persona")
    assert isinstance(persona, dict)
    assert v["persona"] is persona
    assert len(v) == 10                       # bundle 文件清单
    items = dict(v.items())                   # 遍历语义可用（触发全域）
    assert set(AGENTS.loaded_domains("nietzsche")) == {"persona", "memory", "graph", "corpus", "user_model"}
    assert all(items[k] is v[k] for k in items)


def test_r1_concurrent_domain_loads_thread_safe():
    """并发首调不同域 → 每域各加载一次, 无异常/无互踩"""
    errs = []
    tools = [("philosopher_concepts", {"concept": "权力意志"}),
             ("philosopher_memory", {"question": "尼采"}),
             ("philosopher_graph", {"concept": "权力意志"}),
             ("philosopher_user", {"question": "超人"})]
    threads = [threading.Thread(target=lambda t=a, p=ag: _run(t, p, errs)) for a, ag in tools]

    def _run(tool, args, errs):
        try:
            r = _philo(tool)(args)
            assert not r.get("error")
        except Exception as e:    # pragma: no cover
            errs.append(e)
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert not errs, errs
    assert set(AGENTS.loaded_domains("nietzsche")) == {"persona", "memory", "graph", "user_model"}


# ═══════════════════════════════════════════════════════
# R2 — Hybrid Retrieval（embedding mock, 确定性）
# ═══════════════════════════════════════════════════════
def test_r2_dense_ranks_true_vector_first(monkeypatch):
    row = 100
    monkeypatch.setattr(agent_core, "_embed_query", _mock_dense_at(row))
    res = pr.retrieve("任意查询文本（向量被 mock 为 row100）", k=3)
    assert res and res["echoes"], res
    assert res["mode"] == "hybrid"
    assert res["lex_scope"] == "candidates"      # 健康路径: 词法只重排候选, 不整载文本
    assert not pr.state_info()["texts_loaded"]
    assert max(e["scores"]["dense"] for e in res["echoes"]) > 0
    # dense 机制精确性: 用存量向量作 query → 全库余弦 top-1 即该向量自身/并列样板行
    import numpy as np
    pr._ensure_index()
    vecs = np.load(pr.VEC_FILE)
    dense = pr._dense_recall([float(x) for x in vecs[row]], pr._DENSE_CANDIDATES)
    sims = vecs @ (vecs[row] / np.linalg.norm(vecs[row]))
    best = float(sims.max())
    top_set = {int(i) for i in np.where(sims >= best - 1e-5)[0]}
    assert dense and dense[0][0] in top_set      # dense 召回命中自身向量


def test_r2_dense_recall_ordering():
    """dense 召回排序 = 全库余弦降序（前 5 名一致）"""
    import numpy as np
    pr._ensure_index()
    vecs = np.load(pr.VEC_FILE)
    qrow = 3000
    dense = pr._dense_recall([float(x) for x in vecs[qrow]], 8)
    sims = vecs @ (vecs[qrow] / np.linalg.norm(vecs[qrow]))
    expected = [int(i) for i in np.argsort(-sims)[:8] if sims[i] >= pr._DENSE_MIN_SIM]
    assert [r for r, _ in dense][:len(expected)] == expected


def test_r2_echo_metadata_complete(monkeypatch):
    monkeypatch.setattr(agent_core, "_embed_query", _mock_dense_at(0))
    res = pr.retrieve("元数据完整性", k=3)
    for e in res["echoes"]:
        assert e["book"] and e["chapter"]
        assert e["tier"] in ("S", "A", "B", "C")
        assert e["period"] and e["year"]
        assert e["source_type"] and e["source"]
        assert len(e["text"]) <= 220
        assert 0 < e["score"] <= 1.0
        assert isinstance(e["chunk_row"], int)


def test_r2_lexical_degradation_on_429(monkeypatch):
    """embedding 429 → Phase S 词法降级: mode=lexical, 降级原因随结果返回, 词法有召回"""
    def fail_429(q):
        agent_core._embed_status.update({"mode": "lexical", "degraded_reason": "embedding_429_retry_exhausted"})
        return None
    monkeypatch.setattr(agent_core, "_embed_query", fail_429)
    res = pr.retrieve("权力意志", k=3)
    assert res and res["echoes"], "429 降级后词法仍应有召回"
    assert res["mode"] == "lexical"
    assert res["lex_scope"] == "corpus"
    assert "429" in (res.get("degraded_reason") or "")
    assert all(e["scores"]["dense"] == 0.0 for e in res["echoes"])


def test_r2_tool_contract_preserved(monkeypatch):
    """工具 API contract: echoes[{book,chapter,tier,text}] + 新增元数据/retrieval 字段"""
    monkeypatch.setattr(agent_core, "_embed_query", _mock_dense_at(5))
    r = _philo("philosopher_corpus")({"query": "查拉图斯特拉的深渊"})
    assert "error" not in r
    for e in r["echoes"]:
        assert {"book", "chapter", "tier", "text"} <= set(e.keys())
    assert r["retrieval"]["mode"] in ("hybrid", "hybrid_fulllex", "lexical", "lexical_only")
    # Evidence Contract 消费兼容（book/chapter/text/score 全部可提取）
    import evidence_contract as ec
    cands = ec._extract_candidates([
        {"name": "philosopher_corpus", "result_full": r}])
    assert cands, "echoes 应可进入 Evidence Contract 证据池"
    assert all(c["book"] for c in cands)


def test_r2_no_failure_propagation(monkeypatch):
    """检索失败不拖垮 Agent: 空 query → 原 contract 错误提示; 纯标点/无命中词 → 空结果而非异常"""
    monkeypatch.setattr(agent_core, "_embed_query", lambda q: None)
    r = _philo("philosopher_corpus")({"query": ""})
    assert r.get("error") == "缺少检索主题"        # 原有工具 contract 不变
    for q in ["。；、", "qqqqzzzz0000"]:
        r = _philo("philosopher_corpus")({"query": q})
        assert "error" not in r
        assert r.get("echoes") == [] or r.get("echoes")


def test_r2_legacy_fallback_when_artifacts_missing(monkeypatch):
    """索引 artifact 缺失 → 旧 bundle 词法路径兜底（检索不失败, 但会加载 corpus 域）"""
    monkeypatch.setattr(pr, "artifacts_available", lambda: False)
    try:
        r = _philo("philosopher_corpus")({"query": "权力意志"})
        assert "error" not in r
        assert r["retrieval"]["mode"] == "lexical_legacy"
        assert isinstance(r.get("echoes"), list)
        assert "corpus" in AGENTS.loaded_domains("nietzsche")   # 兜底路径允许整载（设计内）
    finally:
        AGENTS.reset_bundle_cache()      # 卸下 453MB 兜底缓存, 不污染其他用例


# ═══════════════════════════════════════════════════════
# R3 — Corpus Access: 精确 chunk 取文, 不整载语料
# ═══════════════════════════════════════════════════════
def test_r3_fetch_chunks_random_access():
    texts = pr.fetch_chunks([0, 100, 6487])
    assert all(isinstance(t, str) and t for t in texts), "按行号 seek 取文应返回非空原文"
    assert pr.state_info()["texts_loaded"] is False, "seek 取文不得整载语料文本"
    assert pr.chunk_text(0) == texts[0]


def test_r3_first_query_avoids_full_corpus_load(monkeypatch):
    """健康路径首问: 只 seek 候选文本, 13.9MB 文本域不加载, 453MB bundle corpus 不加载"""
    monkeypatch.setattr(agent_core, "_embed_query", _mock_dense_at(2000))
    r = _philo("philosopher_corpus")({"query": "whatever"})
    assert r["retrieval"]["lex_scope"] == "candidates"
    assert pr.state_info()["texts_loaded"] is False
    assert "corpus" not in AGENTS.loaded_domains("nietzsche")
    assert r["echoes"]


def test_r3_texts_resident_after_degraded_load(monkeypatch):
    """降级路径整载文本后常驻复用（不重复读盘, 无无界增长）"""
    monkeypatch.setattr(agent_core, "_embed_query", lambda q: None)
    r1 = pr.retrieve("权力意志")
    assert r1["lex_scope"] == "corpus"
    assert pr.state_info()["texts_loaded"]
    r2 = pr.retrieve("永恒轮回")
    assert r2["lex_scope"] == "corpus" and r2["echoes"]
    assert r2["latency_ms"] < 2000, "文本常驻后全语料 BM25 应在秒内"


# ═══════════════════════════════════════════════════════
# 真实 API 冒烟（有 key 才跑; 429 也算通过——降级语义即验收项之一）
# ═══════════════════════════════════════════════════════
def test_r2_real_api_smoke():
    try:                      # 先尝试加载 .env（ZHIPU_API_KEY 可能只存在于 .env）
        from routes.agent import _load_env
        _load_env()
    except Exception:
        pass
    if not os.environ.get("ZHIPU_API_KEY"):
        pytest.skip("ZHIPU_API_KEY 未配置")
    res = pr.retrieve("当你凝视深渊，深渊也回望你", k=3)
    assert res is not None
    assert res["mode"] in ("hybrid", "hybrid_fulllex", "lexical", "lexical_only")
    if res["mode"] in ("hybrid", "hybrid_fulllex"):
        assert res["echoes"] and res["echoes"][0]["scores"]["dense"] > 0
    else:
        # 429/网络受限: 词法降级仍须给出结果或明确空
        assert "degraded_reason" in res
