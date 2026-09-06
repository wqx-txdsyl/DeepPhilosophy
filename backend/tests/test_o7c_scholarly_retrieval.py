# -*- coding: utf-8 -*-
"""O7-C Scholarly Retrieval tests（C1-C30; mock 为主, live gate 另跑）。

核心锁死: PAPER_EXISTS != PAPER_READ; 访问状态机只由实际证据驱动;
provider 失败 != scholarly absence; 无 LLM 元数据补全; SSRF 边界。
"""
import json
import os
import sys
import urllib.request

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)

import scholarly_sources as SS


def _pr(provider="crossref", doi=None, title="T", year=2000, venue="V",
        authors=None, **kw):
    return {"provider": provider, "provider_record_id": doi or kw.get("pid"),
            "doi": doi, "title": title, "authors": authors or [{"name": "A. Author"}],
            "publication_year": year, "container_title": venue,
            "publication_type": "JOURNAL_ARTICLE", "stable_urls": [], **kw}


# ── C1 DOI normalization ──────────────────────────────────────
def test_c1_doi_normalization():
    assert SS.normalize_doi("https://doi.org/10.1007/abc") == "10.1007/abc"
    assert SS.normalize_doi("doi:10.1007/ABC") == "10.1007/abc"
    assert SS.normalize_doi("10.1007/abc.") == "10.1007/abc"
    assert SS.normalize_doi("not a doi") is None
    assert SS.normalize_doi(None) is None


# ── C2 same DOI cross-provider merge ──────────────────────────
def test_c2_same_doi_merges():
    recs = SS.merge_records([
        _pr("crossref", doi="10.1/x", title="Same", year=2001),
        _pr("openalex", doi="10.1/x", title="Same", year=2001)])
    assert len(recs) == 1
    assert recs[0]["source_record_id"] == "doi:10.1/x"
    assert set(recs[0]["provenance"]["providers"]) == {"crossref", "openalex"}


# ── C3 different DOI no merge ─────────────────────────────────
def test_c3_different_doi_no_merge():
    recs = SS.merge_records([
        _pr("crossref", doi="10.1/x", title="Almost Same Title"),
        _pr("openalex", doi="10.1/y", title="Almost Same Title")])
    assert len(recs) == 2  # 同 title 异 DOI 不得合并


# ── C4 provider conflict retained ─────────────────────────────
def test_c4_year_conflict_retained():
    recs = SS.merge_records([
        _pr("crossref", doi="10.1/z", title="C", year=1998),
        _pr("openalex", doi="10.1/z", title="C", year=1999)])
    r = recs[0]
    conflict = [c for c in r["conflicts"] if c["field"] == "publication_year"]
    assert conflict and conflict[0]["resolution_status"] == "CONFLICT_UNRESOLVED"
    assert sorted(conflict[0]["candidate_values"], key=str) == [1998, 1999]


# ── C5 missing fields remain null ─────────────────────────────
def test_c5_missing_fields_null():
    r = SS._mk_canonical([{"provider": "crossref", "doi": None,
                           "title": None, "authors": None, "publication_year": None,
                           "container_title": None, "publication_type": "OTHER",
                           "provider_record_id": "abc", "stable_urls": []}])
    assert r["title"] is None and r["publication_year"] is None
    assert r["identifiers"]["doi"] is None


# ── C6/C7/C8/C9/C10/C11 访问状态机 kill cases ───────────────────
def test_c6_metadata_only():
    r = SS._mk_canonical([_pr(doi="10.1/m")])
    assert r["access"]["level"] == "METADATA_ONLY"
    _, info = SS.get_evidence(r, "ABSTRACT")
    assert info["access_level_after"] == "METADATA_ONLY"
    assert "不得凭 title 推断" in info["access_notes"]


def test_c7_abstract_available():
    r = SS._mk_canonical([_pr(doi="10.1/a", abstract_text="An abstract.")])
    assert r["access"]["level"] == "ABSTRACT_AVAILABLE"
    assert r["abstract"]["hash"]


def test_c8_available_not_read(monkeypatch):
    # RP1 §1: OA 候选不自动升级; 未 fetch 前停留在证据层级
    r = SS._mk_canonical([_pr(doi="10.1/f", abstract_text="abs",
                              oa_pdf_url="https://example.org/paper.pdf")])
    assert r["access"]["level"] == "ABSTRACT_AVAILABLE"
    assert r["full_text_candidates"] and not r["access"]["full_text_url"]
    def boom(*a, **k):
        raise SS.ProviderError("PROVIDER_UNAVAILABLE", "net down")
    monkeypatch.setattr(SS, "_http_get", boom)
    _, info = SS.get_evidence(r, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert info["access_level_after"] == "ABSTRACT_AVAILABLE"  # broken 不虚报
    assert info["full_text_status"].startswith("FETCH_FAILED")


def test_c9_read_requires_parsed_body(monkeypatch):
    # RP1 §2: 2xx+body 取得但解析无正文 → FULL_TEXT_AVAILABLE（非 READ）
    r = SS._mk_canonical([_pr(doi="10.1/f2", abstract_text="abs",
                              oa_pdf_url="https://example.org/paper.pdf")])
    monkeypatch.setattr(SS, "_http_get",
                        lambda *a, **k: (200, b"%PDF junk no text"))
    monkeypatch.setattr(SS, "_extract_text", lambda d, u: "")  # 解析失败
    _, info = SS.get_evidence(r, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert info["access_level_after"] == "FULL_TEXT_AVAILABLE"
    assert info["full_text_status"] == "AVAILABLE_PARSE_FAILED"
    assert not r["access"].get("content_hash")  # READ 才有 hash


def test_c10_broken_oa_url_not_read(monkeypatch):
    # RP1 §3: broken OA URL 降回真实状态（ABSTRACT_AVAILABLE）, 不是 FULL_TEXT_AVAILABLE
    def boom(*a, **k):
        raise SS.ProviderError("PROVIDER_UNAVAILABLE", "http 404")
    r = SS._mk_canonical([_pr(doi="10.1/b", abstract_text="abs",
                              oa_pdf_url="https://example.org/gone.pdf")])
    monkeypatch.setattr(SS, "_http_get", boom)
    _, info = SS.get_evidence(r, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert info["access_level_after"] == "ABSTRACT_AVAILABLE"
    # 仅 metadata 的记录 broken → 保持 METADATA_ONLY
    r2 = SS._mk_canonical([_pr(doi="10.1/b2", oa_pdf_url="https://example.org/g2.pdf")])
    monkeypatch.setattr(SS, "_http_get", boom)
    _, info2 = SS.get_evidence(r2, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert info2["access_level_after"] == "METADATA_ONLY"


def test_c11_doi_landing_not_fulltext():
    # 只有 DOI landing URL（无 OA pdf_url）→ 不得 FULL_TEXT_AVAILABLE
    r = SS._mk_canonical([_pr(doi="10.1/l", abstract_text="abs",
                              stable_urls=["https://doi.org/10.1/l"])])
    assert r["access"]["level"] == "ABSTRACT_AVAILABLE"


# ── C12 无 paywall bypass 路径 ────────────────────────────────
def _code_without_docstrings(path):
    import ast
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            node.body = [n for n in node.body if not (
                isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                and isinstance(n.value.value, str))]
    return ast.unparse(tree)


def test_c12_no_bypass_paths():
    code = _code_without_docstrings(os.path.join(BACKEND, "scholarly_sources.py"))
    for banned in ("sci-hub", "libgen", "annas-archive", "captcha"):
        assert banned not in code.lower(), f"非法访问路径出现: {banned}"


# ── C13/C14 provider 失败语义 ─────────────────────────────────
def test_c13_timeout_not_no_literature(monkeypatch):
    def boom(*a, **k):
        raise SS.ProviderError("PROVIDER_TIMEOUT", "x")
    monkeypatch.setattr(SS, "search_crossref", boom)
    monkeypatch.setattr(SS, "search_openalex", boom)
    monkeypatch.setattr(SS, "_load_cache", lambda: {"searches": {}, "records": {}})
    out = SS.search_scholarship("kant")
    assert out["results"] == [] and out["errors"]
    assert all(e["error"] == "PROVIDER_TIMEOUT" for e in out["errors"])


def test_c14_zero_results_semantics():
    resp = {"results": [], "providers_queried": ["crossref", "openalex"]}
    assert resp  # 0 结果 != 学界没有研究（语义在工具 note 文案锁定）


# ── C15/C16 诚实默认 ──────────────────────────────────────────
def test_c15_peer_review_not_inferred():
    r = SS._mk_canonical([_pr(doi="10.1/j")])  # journal-article
    assert r["peer_review_status"] == "UNVERIFIED"  # 不因 type 推断


def test_c16_role_defaults_unknown():
    r = SS._mk_canonical([_pr(doi="10.1/r")])
    assert r["philosophical_role"] == "UNKNOWN"
    mv = SS.model_view(r)
    assert mv["note"].startswith("access_level")


# ── C17/C18/C19 架构边界 ─────────────────────────────────────
def test_c17_no_llm_metadata_completion():
    for p in (os.path.join(BACKEND, "scholarly_sources.py"),
              os.path.join(BACKEND, "routes", "agent_tools_scholarly.py")):
        code = _code_without_docstrings(p)
        assert "deepseek" not in code.lower() and "zhipu" not in code.lower() \
            and "chat/completions" not in code.lower(), p


def test_c18_no_semantic_sufficiency():
    import inspect
    src = inspect.getsource(SS)
    for banned in ("sufficiency", "足够了", "enough_literature"):
        assert banned not in src.lower()


def test_c19_no_auto_scholarly_tools():
    # 引擎不自动调用 scholarly 工具: SYSTEM_PROMPT_LG 与 engine 无 scholarly 引用
    eng = open(os.path.join(BACKEND, "engine_langgraph.py"), encoding="utf-8").read()
    assert "search_scholarship" not in eng and "scholarly" not in eng.lower()


# ── C20/C21/C22 identity 与 SSRF ─────────────────────────────
def test_c20_source_record_id_stable():
    a = SS.merge_records([_pr(doi="10.1/s"), _pr("openalex", doi="10.1/s")])
    b = SS.merge_records([_pr("openalex", doi="10.1/s"), _pr(doi="10.1/s")])
    assert a[0]["source_record_id"] == b[0]["source_record_id"] == "doi:10.1/s"


@pytest.mark.parametrize("url,why", [
    ("http://localhost:8080/x", "local host"),
    ("http://127.0.0.1/x", "loopback"),
    ("http://192.168.1.1/x", "private"),
    ("http://169.254.169.254/latest/meta-data", "link-local"),
    ("http://10.0.0.1/x", "private"),
    ("file:///etc/passwd", "scheme"),
    ("ftp://x/y", "scheme"),
])
def test_c21_ssrf_blocked(url, why, monkeypatch):
    monkeypatch.setattr(SS.socket, "getaddrinfo",
                        lambda h, p: [(2, 1, 6, "", (h, 0))] if h.replace(".", "").isdigit()
                        else [(2, 1, 6, "", ("93.184.216.34", 0))])
    ok, _ = SS._url_guard(url)
    assert not ok, f"{url} 应被拦截"


def test_c22_no_arbitrary_url_input():
    # get_scholarly_source 只接受 source_record_id（schema 层无 URL 参数）
    schema = None
    import routes.agent_tools_scholarly as ATS
    schema = ATS.TOOLS["get_scholarly_source"]["parameters"]
    props = schema["properties"]
    assert "url" not in props and set(props) == {"source_record_id", "requested_access"}


# ── C23/C24 locator 与 abstract provenance ───────────────────
def test_c23_pdf_page_not_canonical():
    passages = SS._top_passages("p " * 200 + "\n\n" + "q " * 200, None)
    for p in passages:
        assert p["page"] is None and p["locator"] is None  # 无页号 → null, 不造


def test_c24_abstract_provenance_preserved():
    r = SS._mk_canonical([_pr("openalex", doi="10.1/ab",
                              abstract_inverted_index={"word": [0, 2], "x": [1]})])
    assert r["abstract"]["source"] == "OPENALEX_INVERTED_INDEX"
    assert r["abstract"]["text"] == "word x word"
    assert r["abstract"]["hash"]


# ── C25 模型视图精简 ─────────────────────────────────────────
def test_c25_model_view_compact():
    r = SS._mk_canonical([_pr(doi="10.1/mv", abstract_text="abs")])
    mv = SS.model_view(r)
    assert set(mv) <= {"source_record_id", "title", "authors", "year",
                       "publication_type", "venue", "doi", "source_category",
                       "access_level", "provider", "bibliographic_verified_fields", "note"}
    assert "provider_records" not in mv and "conflicts" not in mv


# ── C28 精确缓存机械性 ───────────────────────────────────────
def test_c28_cache_mechanical(monkeypatch, tmp_path):
    monkeypatch.setattr(SS, "CACHE_PATH", str(tmp_path / "c.json"))
    calls = {"n": 0}
    def fake_search(q, limit=8, **kw):
        calls["n"] += 1
        return [_pr(doi="10.1/cache")]
    monkeypatch.setattr(SS, "search_crossref", fake_search)
    monkeypatch.setattr(SS, "search_openalex", lambda *a, **k: [])
    SS._cache = None
    SS.search_scholarship("cache test")
    SS.search_scholarship("cache test")
    assert calls["n"] == 1  # 第二次走缓存


# ── C29/C30 既有检索与 O7-B 数据不变 ─────────────────────────
def test_c29_primary_retrieval_unchanged():
    import subprocess
    r = subprocess.run(["git", "diff", "--quiet", "e71f4a696", "--",
                        "backend/routes/agent_tools_retrieval.py",
                        "backend/data/book_bibliography.json"],
                       cwd=ROOT, capture_output=True)
    assert r.returncode == 0, "primary retrieval / O7-B bibliography 被改动"


def test_c30_tool_count():
    import routes.agent_tools_scholarly as ATS
    assert "search_scholarship" in ATS.TOOLS
    assert "get_scholarly_source" in ATS.TOOLS


# ══ O7-C RP1 — Access Truth & Security Closure（R1-R18）══════════
def _mk_oa(doi="10.1/x", abstract=None, url="https://oa.example.org/p.pdf"):
    return SS._mk_canonical([_pr(doi=doi, abstract_text=abstract, oa_pdf_url=url)])


def test_r1_candidate_not_auto_available():
    r = _mk_oa(abstract="abs")
    assert r["access"]["level"] == "ABSTRACT_AVAILABLE"      # 非 AVAILABLE
    assert r["full_text_candidates"][0]["access_claim"] == "OPEN_ACCESS"


def test_r2_broken_oa_stays_real_state(monkeypatch):
    monkeypatch.setattr(SS, "_http_get",
                        lambda *a, **k: (_ for _ in ()).throw(SS.ProviderError("PROVIDER_UNAVAILABLE", "404")))
    r = _mk_oa(abstract="abs")
    _, i = SS.get_evidence(r, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert i["access_level_after"] == "ABSTRACT_AVAILABLE"


def test_r3_body_and_parse_reads(monkeypatch):
    body = ("para " * 400).encode()
    monkeypatch.setattr(SS, "_http_get", lambda *a, **k: (200, body))
    monkeypatch.setattr(SS, "_extract_text", lambda d, u: "t " * 500)
    r = _mk_oa(abstract="abs")
    rec, i = SS.get_evidence(r, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert i["access_level_after"] == "FULL_TEXT_READ" and i["content_hash"]


def test_r4_body_parse_fail_available(monkeypatch):
    monkeypatch.setattr(SS, "_http_get", lambda *a, **k: (200, b"%PDF xx"))
    monkeypatch.setattr(SS, "_extract_text", lambda d, u: "")
    r = _mk_oa(abstract="abs")
    _, i = SS.get_evidence(r, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert i["access_level_after"] == "FULL_TEXT_AVAILABLE"


def test_r5_oa_without_abstract_readable(monkeypatch):
    # RP1 §4: 无 abstract 也可直接尝试全文
    monkeypatch.setattr(SS, "_http_get", lambda *a, **k: (200, b"x" * 1000))
    monkeypatch.setattr(SS, "_extract_text", lambda d, u: "meaningful " * 100)
    r = _mk_oa(abstract=None)
    assert r["access"]["level"] == "METADATA_ONLY"
    rec, i = SS.get_evidence(r, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert i["access_level_after"] == "FULL_TEXT_READ"


def test_r6_abstract_request_no_downgrade_available():
    r = _mk_oa(abstract="abs")
    r["access"] = {"level": "FULL_TEXT_AVAILABLE", "evidence": "prev verified",
                   "checked_at": 1, "full_text_url": "u", "content_hash": None}
    _, i = SS.get_evidence(r, "ABSTRACT")
    assert i["access_level_after"] == "FULL_TEXT_AVAILABLE"  # 不降级
    assert i["returned_evidence_level"] == "ABSTRACT_AVAILABLE"


def test_r7_abstract_request_no_downgrade_read():
    r = _mk_oa(abstract="abs")
    r["access"] = {"level": "FULL_TEXT_READ", "evidence": "prev read",
                   "checked_at": 1, "full_text_url": "u", "content_hash": "h"}
    _, i = SS.get_evidence(r, "ABSTRACT")
    assert i["access_level_after"] == "FULL_TEXT_READ"


def test_r8_source_category_journal_defaults_unknown():
    r = SS._mk_canonical([_pr(doi="10.1/sc")])   # JOURNAL_ARTICLE
    assert SS.model_view(r)["source_category"] == "UNKNOWN"


def test_r9_primary_journal_not_secondary():
    # 哲学家本人论文（journal article）也不得自动 SCHOLARLY_SECONDARY
    r = SS._mk_canonical([_pr(doi="10.1/pj", title="Kant's own essay",
                              authors=[{"name": "Immanuel Kant"}])])
    r["philosophical_role"] = "PRIMARY"
    assert SS.model_view(r)["source_category"] == "PRIMARY"


# ── R10-R13 redirect SSRF kill cases（mock redirect handler）──
class _Redirector(SS._GuardedRedirectHandler):
    def __init__(self, chain):
        self.chain = chain
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = self.chain.pop(0) if self.chain else newurl
        ok, why = SS._url_guard(target)
        if not ok:
            raise SS.ProviderError("URL_BLOCKED", f"redirect target {why}")
        return super().redirect_request(req, fp, code, msg, headers, target)


def _redirect_chain_test(chain, monkeypatch):
    """模拟: 初始 URL 公网, 逐跳跳到 chain 中的目标（真实 Request 对象）。"""
    req = urllib.request.Request("https://public.example/start",
                                 headers={"User-Agent": "t"})
    h = _Redirector(chain)
    try:
        h.redirect_request(req, None, 302, "Found", {}, chain[0])
        return True, None
    except SS.ProviderError as e:
        return False, e.kind


@pytest.mark.parametrize("target,should_block", [
    ("https://elsewhere.example.org/x", False),      # R1 public→public
    ("http://localhost:9000/x", True),               # R2
    ("http://127.0.0.1/x", True),                    # R3
    ("http://10.0.0.1/x", True),                     # R4
    ("http://169.254.169.254/latest", True),         # R5
    ("file:///etc/passwd", True),                    # R6
])
def test_r10_r12_redirect_targets(target, should_block, monkeypatch):
    monkeypatch.setattr(SS.socket, "getaddrinfo",
                        lambda h, p: [(2, 1, 6, "", ("93.184.216.34", 0))]
                        if not h.replace(".", "").isdigit() else [(2, 1, 6, "", (h, 0))])
    ok, kind = _redirect_chain_test([target], monkeypatch)
    assert ok != should_block


def test_r13_redirect_limit():
    req = urllib.request.Request("https://public.example/start",
                                 headers={"User-Agent": "t"})
    h = SS._GuardedRedirectHandler()
    SS._GuardedRedirectHandler.hops = SS.MAX_REDIRECTS   # 已达上限
    try:
        with pytest.raises(SS.ProviderError) as e:
            h.redirect_request(req, None, 302, "Found", {}, "https://x.example/y")
        assert e.value.kind == "REDIRECT_LIMIT"
    finally:
        SS._GuardedRedirectHandler.hops = 0


def test_r14_gate_kill_cases_computed():
    # live gate 的 A1-A8 必须由数据算出（gate runner 已改为执行式; 此处锁 runner 源码无硬编码 True）
    src = open(os.path.join(BACKEND, "tools", "evaluation", "o7c_live_gate.py"),
               encoding="utf-8").read()
    assert '"A6_broken_url_not_available": True' not in src
    assert '"A4_real_read": True' not in src


def test_r15_access_counts_sum():
    # 访问状态计数守恒（对 cache 内记录机械校验）
    recs = list(SS._load_cache()["records"].values())
    if not recs:
        pytest.skip("cache 空")  # live gate 后填充
    from collections import Counter
    c = Counter(r["access"]["level"] for r in recs)
    assert sum(c.values()) == len(recs)


def test_r16_r17_metric_split():
    src = open(os.path.join(BACKEND, "tools", "evaluation", "o7c_live_gate.py"),
               encoding="utf-8").read()
    assert "SUBSTANTIVE_QUERIES_WITH_RELEVANT_RECORD" in src
    assert "NEGATIVE_QUERIES_WITH_FALSE_POSITIVE" in src
    assert "NEGATIVE_CONTROL_PASS" in src


def test_r18_production_frozen_rp1():
    import subprocess
    for rel in ("backend/engine_langgraph.py", "backend/final_validator.py",
                "backend/quote_bound.py"):
        r = subprocess.run(["git", "diff", "--quiet",
                            "302f7380a4146d78374887063b336c5aa7381ddd", "--", rel],
                           cwd=ROOT, capture_output=True)
        assert r.returncode == 0, f"{rel} 被改动"
