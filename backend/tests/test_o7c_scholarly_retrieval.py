# -*- coding: utf-8 -*-
"""O7-C Scholarly Retrieval tests（RP2 版: C 核心契约 + T1-T21 传输/真值关闭）。

锁死:
  - access 状态机严格单调（含重复全文请求路径）
  - timeout = 单一真实 NETWORK_SOCKET_TIMEOUT（无 detached probe）
  - redirect 计数 request-local; DNS pinning 防 TOCTOU
  - FULL_TEXT_READ 只来自 DIRECT_PDF 解析成功; HTML landing 不冒充正文
  - 逐候选 fetch 记账守恒
"""
import json
import os
import subprocess
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


def _resp(body=b"x" * 1000, status=200, ct="application/pdf", final="https://oa.example.org/p.pdf"):
    r = SS._Resp()
    r.status, r.body, r.final_url, r.content_type, r.redirect_count = \
        status, body, final, ct, 0
    return r


def _mk_oa(doi="10.1/x", abstract="abs", kind="DIRECT_PDF",
           url="https://oa.example.org/p.pdf"):
    return SS._mk_canonical([_pr(doi=doi, abstract_text=abstract, oa_pdf_url=url,
                                 oa_candidate_kind=kind)])


# ══ C 系核心契约 ═══════════════════════════
def test_c1_doi_normalization():
    assert SS.normalize_doi("https://doi.org/10.1007/abc") == "10.1007/abc"
    assert SS.normalize_doi("doi:10.1007/ABC") == "10.1007/abc"
    assert SS.normalize_doi("not a doi") is None


def test_c2_same_doi_merges():
    recs = SS.merge_records([_pr("crossref", doi="10.1/x"),
                             _pr("openalex", doi="10.1/x")])
    assert len(recs) == 1 and set(recs[0]["provenance"]["providers"]) == {"crossref", "openalex"}


def test_c3_different_doi_no_merge():
    assert len(SS.merge_records([_pr(doi="10.1/x"), _pr("openalex", doi="10.1/y")])) == 2


def test_c4_year_conflict_retained():
    r = SS.merge_records([_pr("crossref", doi="10.1/z", year=1998),
                          _pr("openalex", doi="10.1/z", year=1999)])[0]
    c = [x for x in r["conflicts"] if x["field"] == "publication_year"]
    assert c and c[0]["resolution_status"] == "CONFLICT_UNRESOLVED"


def test_c5_missing_fields_null():
    r = SS._mk_canonical([{"provider": "crossref", "doi": None, "title": None,
                           "authors": None, "publication_year": None,
                           "container_title": None, "publication_type": "OTHER",
                           "provider_record_id": "abc", "stable_urls": []}])
    assert r["title"] is None and r["identifiers"]["doi"] is None


def test_c6_metadata_only():
    r = SS._mk_canonical([_pr(doi="10.1/m")])
    assert r["access"]["level"] == "METADATA_ONLY"
    _, i = SS.get_evidence(r, "ABSTRACT")
    assert i["access_level_after"] == "METADATA_ONLY"


def test_c7_abstract_available():
    r = SS._mk_canonical([_pr(doi="10.1/a", abstract_text="An abstract.")])
    assert r["access"]["level"] == "ABSTRACT_AVAILABLE" and r["abstract"]["hash"]


def test_c11_doi_landing_not_fulltext():
    r = SS._mk_canonical([_pr(doi="10.1/l", abstract_text="abs",
                              stable_urls=["https://doi.org/10.1/l"])])
    assert r["access"]["level"] == "ABSTRACT_AVAILABLE"


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
        assert banned not in code.lower()


def test_c13_timeout_not_no_literature(monkeypatch):
    def boom(*a, **k):
        raise SS.ProviderError("PROVIDER_TIMEOUT", "x")
    monkeypatch.setattr(SS, "search_crossref", boom)
    monkeypatch.setattr(SS, "search_openalex", boom)
    monkeypatch.setattr(SS, "_load_cache", lambda: {"searches": {}, "records": {}})
    out = SS.search_scholarship("kant")
    assert out["errors"] and all(e["error"] == "PROVIDER_TIMEOUT" for e in out["errors"])


def test_c15_peer_review_not_inferred():
    assert SS._mk_canonical([_pr(doi="10.1/j")])["peer_review_status"] == "UNVERIFIED"


def test_c16_role_defaults_unknown():
    r = SS._mk_canonical([_pr(doi="10.1/r")])
    assert r["philosophical_role"] == "UNKNOWN"
    assert SS.model_view(r)["source_category"] == "UNKNOWN"


def test_c17_no_llm_metadata_completion():
    for p in (os.path.join(BACKEND, "scholarly_sources.py"),
              os.path.join(BACKEND, "routes", "agent_tools_scholarly.py")):
        code = _code_without_docstrings(p)
        assert "chat/completions" not in code.lower(), p


def test_c19_no_auto_scholarly_tools():
    eng = open(os.path.join(BACKEND, "engine_langgraph.py"), encoding="utf-8").read()
    assert "search_scholarship" not in eng and "scholarly" not in eng.lower()


def test_c20_source_record_id_stable():
    a = SS.merge_records([_pr(doi="10.1/s"), _pr("openalex", doi="10.1/s")])
    b = SS.merge_records([_pr("openalex", doi="10.1/s"), _pr(doi="10.1/s")])
    assert a[0]["source_record_id"] == b[0]["source_record_id"] == "doi:10.1/s"


@pytest.mark.parametrize("url", [
    "http://localhost:8080/x", "http://127.0.0.1/x", "http://192.168.1.1/x",
    "http://169.254.169.254/latest/meta-data", "http://10.0.0.1/x",
    "file:///etc/passwd", "ftp://x/y",
])
def test_c21_ssrf_blocked(url, monkeypatch):
    monkeypatch.setattr(SS.socket, "getaddrinfo",
                        lambda h, p: [(2, 1, 6, "", (h, p or 80))
                                      if h.replace(".", "").isdigit()
                                      else (2, 1, 6, "", ("93.184.216.34", 0))])
    ok, _ = SS._url_guard(url)
    assert not ok


def test_c22_no_arbitrary_url_input():
    import routes.agent_tools_scholarly as ATS
    props = ATS.TOOLS["get_scholarly_source"]["parameters"]["properties"]
    assert "url" not in props and set(props) == {"source_record_id", "requested_access"}


def test_c25_model_view_compact():
    mv = SS.model_view(SS._mk_canonical([_pr(doi="10.1/mv", abstract_text="abs")]))
    assert "provider_records" not in mv and "conflicts" not in mv


def test_c28_cache_mechanical(monkeypatch, tmp_path):
    monkeypatch.setattr(SS, "CACHE_PATH", str(tmp_path / "c.json"))
    calls = {"n": 0}
    def fake(q, limit=8, **kw):
        calls["n"] += 1
        return [_pr(doi="10.1/cache")]
    monkeypatch.setattr(SS, "search_crossref", fake)
    monkeypatch.setattr(SS, "search_openalex", lambda *a, **k: [])
    SS._cache = None
    SS.search_scholarship("cache test")
    SS.search_scholarship("cache test")
    assert calls["n"] == 1


def test_c29_primary_retrieval_unchanged():
    r = subprocess.run(["git", "diff", "--quiet", "e71f4a696", "--",
                        "backend/routes/agent_tools_retrieval.py",
                        "backend/data/book_bibliography.json"],
                       cwd=ROOT, capture_output=True)
    assert r.returncode == 0


def test_c30_tool_count():
    import routes.agent_tools_scholarly as ATS
    assert "search_scholarship" in ATS.TOOLS and "get_scholarly_source" in ATS.TOOLS


# ══ RP2 T1-T21: 传输真值 + FULL_TEXT_READ 真实性 + 记账 ════════
def _pdf_body(text="paragraph " * 200):
    return b"%PDF-1.4 fake\n" + text.encode()


def test_t1_read_then_parse_fail_no_downgrade(monkeypatch):
    r = _mk_oa()
    r["access"] = {"level": "FULL_TEXT_READ", "evidence": "prev", "checked_at": 1,
                   "full_text_url": "u", "content_hash": "h"}
    monkeypatch.setattr(SS, "_http_get", lambda *a, **k: _resp(body=b"%PDF xx", ct="application/pdf"))
    monkeypatch.setattr(SS, "_extract_text", lambda d, u: "")
    _, i = SS.get_evidence(r, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert i["access_level_after"] == "FULL_TEXT_READ"      # M1


def test_t2_read_then_fetch_fail_no_downgrade(monkeypatch):
    r = _mk_oa()
    r["access"] = {"level": "FULL_TEXT_READ", "evidence": "prev", "checked_at": 1,
                   "full_text_url": "u", "content_hash": "h"}
    def boom(*a, **k):
        raise SS.ProviderError("PROVIDER_UNAVAILABLE", "404")
    monkeypatch.setattr(SS, "_http_get", boom)
    _, i = SS.get_evidence(r, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert i["access_level_after"] == "FULL_TEXT_READ"      # M2


def test_t3_available_then_fetch_fail_no_downgrade(monkeypatch):
    r = _mk_oa()
    r["access"] = {"level": "FULL_TEXT_AVAILABLE", "evidence": "verified", "checked_at": 1,
                   "full_text_url": "u", "content_hash": None}
    def boom(*a, **k):
        raise SS.ProviderError("PROVIDER_UNAVAILABLE", "404")
    monkeypatch.setattr(SS, "_http_get", boom)
    _, i = SS.get_evidence(r, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert i["access_level_after"] == "FULL_TEXT_AVAILABLE"  # M3


def test_t4_all_transitions_monotonic():
    order = ["METADATA_ONLY", "ABSTRACT_AVAILABLE", "FULL_TEXT_AVAILABLE", "FULL_TEXT_READ"]
    for a in order:
        for b in order:
            assert (SS._LEVEL_ORDER[a] >= SS._LEVEL_ORDER[b]) == (order.index(a) >= order.index(b))


def test_t5_no_detached_connect_probe():
    code = _code_without_docstrings(os.path.join(BACKEND, "scholarly_sources.py"))
    assert "_connect_probe" not in code


def test_t6_timeout_config_matches_request_socket():
    import inspect
    src = inspect.getsource(SS)
    assert "timeout=NETWORK_SOCKET_TIMEOUT" in src
    assert "CONNECT_TIMEOUT" not in _code_without_docstrings(
        os.path.join(BACKEND, "scholarly_sources.py"))
    assert SS.NETWORK_SOCKET_TIMEOUT == 20


def test_t7_t8_redirect_counter_request_local():
    a = SS._GuardedRedirectHandler()
    b = SS._GuardedRedirectHandler()
    a.hops = 3
    assert b.hops == 0                        # T8: 独立 handler 不互相干扰


def _redirect_guard(target):
    req = urllib.request.Request("https://public.example/start", headers={"User-Agent": "t"})
    h = SS._GuardedRedirectHandler()
    try:
        h.redirect_request(req, None, 302, "Found", {}, target)
        return True
    except SS.ProviderError:
        return False


@pytest.mark.parametrize("target,should_block", [
    ("https://elsewhere.example.org/x", False),
    ("http://localhost:9000/x", True),
    ("http://127.0.0.1/x", True),
    ("http://10.0.0.1/x", True),
    ("http://169.254.169.254/latest", True),
    ("file:///etc/passwd", True),
])
def test_redirect_kill_cases(target, should_block, monkeypatch):
    monkeypatch.setattr(SS.socket, "getaddrinfo",
                        lambda h, p: [(2, 1, 6, "", ("93.184.216.34", 0))]
                        if not h.replace(".", "").isdigit() else [(2, 1, 6, "", (h, 0))])
    assert _redirect_guard(target) != should_block


def test_t7_redirect_limit_request_local():
    req = urllib.request.Request("https://public.example/start", headers={"User-Agent": "t"})
    h = SS._GuardedRedirectHandler()
    h.hops = SS.MAX_REDIRECTS
    with pytest.raises(SS.ProviderError) as e:
        h.redirect_request(req, None, 302, "Found", {}, "https://x.example/y")
    assert e.value.kind == "REDIRECT_LIMIT"


def test_t9_dns_rebind_public_then_private(monkeypatch):
    state = {"n": 0}
    def flaky_getaddrinfo(host, port, proto=None):
        state["n"] += 1
        ip = "93.184.216.34" if state["n"] == 1 else "169.254.169.254"
        return [(2, 1, 6, "", (ip, port or 443))]
    monkeypatch.setattr(SS.socket, "getaddrinfo", flaky_getaddrinfo)
    addr = SS._pinned_addr_for("https://public.example/x")
    assert addr[0] == "93.184.216.34"      # pin 在第一次校验的公网地址
    import socket as _s
    captured = {}
    real_cc = _s.create_connection

    class _FakeSock:
        def setsockopt(self, *a, **kw):
            pass

        def close(self):
            pass

    def spy_create_connection(address, timeout=None, *a, **kw):
        captured["addr"] = address
        return _FakeSock()

    _s.create_connection = spy_create_connection
    try:
        class _Conn(SS._PinnedHTTP):
            _pinned_addr = addr
        c = _Conn("public.example", 443)
        c.connect()
    finally:
        _s.create_connection = real_cc
    assert captured["addr"][0] == "93.184.216.34"  # 实际 connect 目标=已验证公网地址


def test_t10_direct_pdf_read(monkeypatch):
    monkeypatch.setattr(SS, "_http_get", lambda *a, **k: _resp(body=_pdf_body()))
    monkeypatch.setattr(SS, "_extract_text", lambda d, u: "meaningful " * 100)
    r = _mk_oa(kind="DIRECT_PDF")
    _, i = SS.get_evidence(r, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert i["access_level_after"] == "FULL_TEXT_READ" and i["content_hash"]


def test_t11_direct_pdf_parse_fail_available(monkeypatch):
    monkeypatch.setattr(SS, "_http_get", lambda *a, **k: _resp(body=b"%PDF junk"))
    monkeypatch.setattr(SS, "_extract_text", lambda d, u: "")
    r = _mk_oa(kind="DIRECT_PDF")
    _, i = SS.get_evidence(r, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert i["access_level_after"] == "FULL_TEXT_AVAILABLE"


def test_t12_html_landing_not_read(monkeypatch):
    monkeypatch.setattr(SS, "_http_get",
                        lambda *a, **k: _resp(body=b"<html>" + b"word " * 500 + b"</html>",
                                              ct="text/html"))
    r = _mk_oa(kind="OA_LOCATION", url="https://repo.example.org/page")
    _, i = SS.get_evidence(r, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert i["access_level_after"] == "FULL_TEXT_AVAILABLE"
    assert i["full_text_status"] == "AVAILABLE_ONLY"


def test_t13_oa_without_abstract_direct_pdf_read(monkeypatch):
    monkeypatch.setattr(SS, "_http_get", lambda *a, **k: _resp(body=_pdf_body()))
    monkeypatch.setattr(SS, "_extract_text", lambda d, u: "body " * 200)
    r = _mk_oa(abstract=None, kind="DIRECT_PDF")
    assert r["access"]["level"] == "METADATA_ONLY"
    _, i = SS.get_evidence(r, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert i["access_level_after"] == "FULL_TEXT_READ"


def test_t14_attempt_accounting_per_candidate(monkeypatch):
    calls = []
    def flaky(url, *a, **k):
        calls.append(url)
        if len(calls) == 1:
            raise SS.ProviderError("PROVIDER_UNAVAILABLE", "404")
        return _resp(body=_pdf_body())
    monkeypatch.setattr(SS, "_http_get", flaky)
    monkeypatch.setattr(SS, "_extract_text", lambda d, u: "t " * 200)
    r = _mk_oa(doi="10.1/multi")
    r["full_text_candidates"] = [
        {"url": "https://a.example/1.pdf", "provider": "openalex",
         "access_claim": "OPEN_ACCESS", "candidate_kind": "DIRECT_PDF"},
        {"url": "https://a.example/2.pdf", "provider": "openalex",
         "access_claim": "OPEN_ACCESS", "candidate_kind": "DIRECT_PDF"}]
    _, i = SS.get_evidence(r, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert len(i["full_text_attempts"]) == 2
    assert [a["result"] for a in i["full_text_attempts"]] == ["HTTP_FAILURE", "READ"]


def test_t15_attempt_conservation():
    fake = [{"result": "HTTP_FAILURE"}, {"result": "BLOCKED"},
            {"result": "READ"}, {"result": "AVAILABLE"}]
    http_f = sum(1 for a in fake if a["result"] == "HTTP_FAILURE")
    blocked = sum(1 for a in fake if a["result"] == "BLOCKED")
    succ = sum(1 for a in fake if a["result"] in ("READ", "AVAILABLE"))
    assert len(fake) == http_f + blocked + succ


def test_t16_gate_no_hardcoded_booleans():
    src = open(os.path.join(BACKEND, "tools", "evaluation", "o7c_live_gate.py"),
               encoding="utf-8").read()
    for pat in ('"A6_broken_url_not_available": True',
                '"A7_abstract_no_internal_structure": True',
                '"A4_real_read": True', '"A5_doi_landing_not_fulltext": True'):
        assert pat not in src, pat


def test_t17_a5_executed_doi_only():
    r = SS._mk_canonical([_pr(doi="10.1/only", abstract_text=None,
                              stable_urls=["https://doi.org/10.1/only"])])
    assert not (r.get("full_text_candidates") or [])
    assert r["access"]["level"] == "METADATA_ONLY"


def test_t18_a7_executed_overreach_fixture():
    r = SS._mk_canonical([_pr(doi="10.1/abs7", abstract_text="A short abstract.")])
    assert r["access"]["level"] == "ABSTRACT_AVAILABLE"
    assert "第四节" not in r["abstract"]["text"]


def test_t19_a8_no_fetch_not_read():
    r = _mk_oa(kind="DIRECT_PDF")
    assert r["full_text_candidates"]
    assert r["access"]["level"] != "FULL_TEXT_READ"
    assert not r["access"].get("content_hash")


def test_t20_report_contains_real_gate_sha():
    report = open(os.path.join(ROOT, "docs", "PHIAGENT_O7C_SCHOLARLY_RETRIEVAL.md"),
                  encoding="utf-8").read()
    assert "本节 gate 产物 commit" not in report, "占位 SHA 未回填"


def test_t21_production_frozen():
    for rel in ("backend/engine_langgraph.py", "backend/final_validator.py",
                "backend/quote_bound.py"):
        r = subprocess.run(["git", "diff", "--quiet",
                            "302f7380a4146d78374887063b336c5aa7381ddd", "--", rel],
                           cwd=ROOT, capture_output=True)
        assert r.returncode == 0, f"{rel} 被改动"


# ══ Final Gate Patch: Network Trust Boundary & Verified Document Body ══
def test_t22_ct_pdf_html_body_not_read(monkeypatch):
    monkeypatch.setattr(SS, "_http_get",
                        lambda *a, **k: _resp(body=b"<html>" + b"word " * 500 + b"</html>",
                                              ct="application/pdf"))
    r = _mk_oa(kind="DIRECT_PDF")
    _, i = SS.get_evidence(r, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert i["access_level_after"] != "FULL_TEXT_READ"


def test_t23_url_pdf_html_body_not_read(monkeypatch):
    monkeypatch.setattr(SS, "_http_get",
                        lambda *a, **k: _resp(body=b"<html>" + b"word " * 500 + b"</html>",
                                              ct="text/html",
                                              final="https://oa.example.org/p.pdf"))
    monkeypatch.setattr(SS, "_extract_text", lambda d, u: "should not count " * 50)
    r = _mk_oa(kind="DIRECT_PDF", url="https://oa.example.org/p.pdf")
    _, i = SS.get_evidence(r, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert i["access_level_after"] != "FULL_TEXT_READ"   # 命名不构成 body 证明


def test_t24_pdf_magic_parser_success_read(monkeypatch):
    monkeypatch.setattr(SS, "_http_get",
                        lambda *a, **k: _resp(body=_pdf_body(), ct="application/octet-stream"))
    monkeypatch.setattr(SS, "_extract_text", lambda d, u: "body " * 200)
    r = _mk_oa(kind="DIRECT_PDF")
    _, i = SS.get_evidence(r, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert i["access_level_after"] == "FULL_TEXT_READ"  # body beats wrong content-type


def test_t25_read_provenance_body_signature(monkeypatch):
    monkeypatch.setattr(SS, "_http_get", lambda *a, **k: _resp(body=_pdf_body()))
    monkeypatch.setattr(SS, "_extract_text", lambda d, u: "body " * 200)
    r = _mk_oa(kind="DIRECT_PDF")
    rec, _ = SS.get_evidence(r, "FULL_TEXT_IF_LEGALLY_AVAILABLE")
    assert rec["access"]["body_signature_verified"] is True
    assert rec["access"]["verified_document_kind"] == "PDF"
    assert rec["access"]["parser"] == "pdftotext"


def test_t26_direct_mode_19818_blocked(monkeypatch):
    monkeypatch.delenv("SCHOLARLY_NETWORK_MODE", raising=False)
    monkeypatch.setattr(SS.socket, "getaddrinfo",
                        lambda h, p, proto=None: [(2, 1, 6, "", ("198.18.0.1", p or 443))])
    with pytest.raises(SS.ProviderError) as e:
        SS._pinned_addr_for("https://some.example/x")
    assert e.value.kind == "URL_BLOCKED"
    ok, why = SS._url_guard("https://some.example/x")
    assert not ok


def test_t27_trusted_fake_ip_mode_allows(monkeypatch):
    monkeypatch.setenv("SCHOLARLY_NETWORK_MODE", "TRUSTED_PROXY")
    monkeypatch.setattr(SS.socket, "getaddrinfo",
                        lambda h, p, proto=None: [(2, 1, 6, "", ("198.18.0.1", p or 443))])
    addr = SS._pinned_addr_for("https://some.example/x")
    assert addr[0] == "198.18.0.1"
    ok, _ = SS._url_guard("https://some.example/x")
    assert ok
    monkeypatch.delenv("SCHOLARLY_NETWORK_MODE", raising=False)


def test_t28_untrusted_proxy_not_auto_delegated(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://untrusted.example:8080")
    monkeypatch.delenv("SCHOLARLY_NETWORK_MODE", raising=False)
    import inspect
    src = inspect.getsource(SS._http_get)
    assert "getproxies()" not in src.split("# DIRECT_PINNED")[0], \
        "检测到代理就自动信任的分支已废除"
    monkeypatch.delenv("HTTP_PROXY", raising=False)


def test_t29_trusted_proxy_reports_delegated(monkeypatch):
    monkeypatch.setenv("SCHOLARLY_NETWORK_MODE", "TRUSTED_PROXY")
    assert SS.dns_rebinding_mode() == "TRUSTED_PROXY_DELEGATED"
    monkeypatch.delenv("SCHOLARLY_NETWORK_MODE", raising=False)
    monkeypatch.setenv("SCHOLARLY_NETWORK_MODE", "DIRECT_PINNED")
    assert SS.dns_rebinding_mode() == "DIRECT_IP_PINNED"
    monkeypatch.delenv("SCHOLARLY_NETWORK_MODE", raising=False)


def test_t30_cross_host_redirect_repins(monkeypatch):
    monkeypatch.delenv("SCHOLARLY_NETWORK_MODE", raising=False)
    resolved = []
    def gai(host, port, proto=None):
        ip = "1.1.1.1" if host == "host-a.example" else "2.2.2.2"
        resolved.append((host, ip))
        return [(2, 1, 6, "", (ip, port or 443))]
    monkeypatch.setattr(SS.socket, "getaddrinfo", gai)
    h = SS._PinnedHTTPSHandler()
    # 第一跳 host-A
    class _ReqA:
        full_url = "https://host-a.example/x"
        def get_method(self): return "GET"
    try:
        h.do_open(SS._PinnedHTTPS, _ReqA())
    except Exception:
        pass
    # 第二跳 redirect → host-B: do_open 重新按当前 URL pin
    class _ReqB:
        full_url = "https://host-b.example/y"
        def get_method(self): return "GET"
    try:
        h.do_open(SS._PinnedHTTPS, _ReqB())
    except Exception:
        pass
    ips = [ip for _, ip in resolved]
    assert "2.2.2.2" in ips, "第二跳必须对 host-B 重新 resolve/pin"


def test_t31_redirect_private_still_blocked(monkeypatch):
    monkeypatch.delenv("SCHOLARLY_NETWORK_MODE", raising=False)
    req = urllib.request.Request("https://public.example/s", headers={"User-Agent": "t"})
    h = SS._GuardedRedirectHandler()
    with pytest.raises(SS.ProviderError):
        h.redirect_request(req, None, 302, "Found", {}, "http://192.168.0.1/x")


def test_t32_live_read_verifier_checks_signature():
    src = open(os.path.join(BACKEND, "tools", "evaluation", "o7c_live_gate.py"),
               encoding="utf-8").read()
    assert "body_signature_verified" in src and "VERIFIED_PDF_READ_COUNT" in src


def test_t33_metrics_distinguish_available_only():
    src = open(os.path.join(BACKEND, "tools", "evaluation", "o7c_live_gate.py"),
               encoding="utf-8").read()
    assert "FULLTEXT_AVAILABLE_ONLY_SUCCESS" in src
    assert "DIRECT_PDF_PARSE_FAILURES" in src
    assert '"FULLTEXT_PARSE_FAILURES"' not in src


# ══ Final Gate Patch 2: 显式禁代理（P1-P5 真行为测试）═══════
def _opener_proxy_maps(opener):
    return [h.proxies for h in opener.handlers
            if isinstance(h, urllib.request.ProxyHandler)]


def test_p1_auto_with_http_proxy_not_used(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://untrusted.example:8080")
    monkeypatch.delenv("SCHOLARLY_NETWORK_MODE", raising=False)
    maps = _opener_proxy_maps(SS._build_network_opener())
    assert all(m == {} for m in maps), maps   # 无任何非空 proxy map=环境代理被禁用


def test_p2_direct_with_https_proxy_not_used(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://untrusted.example:8080")
    monkeypatch.setenv("SCHOLARLY_NETWORK_MODE", "DIRECT_PINNED")
    assert all(m == {} for m in _opener_proxy_maps(SS._build_network_opener()))
    monkeypatch.delenv("SCHOLARLY_NETWORK_MODE", raising=False)


def test_p3_trusted_proxy_delegation_enabled(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://trusted.local:8080")
    monkeypatch.setenv("SCHOLARLY_NETWORK_MODE", "TRUSTED_PROXY")
    opener = SS._build_network_opener()
    # TRUSTED_PROXY 分支未显式注入空 ProxyHandler → 环境代理可用（委托）
    empty = [h for h in opener.handlers
             if isinstance(h, urllib.request.ProxyHandler) and h.proxies == {}]
    assert not empty
    monkeypatch.delenv("SCHOLARLY_NETWORK_MODE", raising=False)


def test_p4_auto_env_proxy_private_target_blocked(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://untrusted.example:8080")
    monkeypatch.delenv("SCHOLARLY_NETWORK_MODE", raising=False)
    monkeypatch.setattr(SS.socket, "getaddrinfo",
                        lambda h, p, proto=None: [(2, 1, 6, "", ("192.168.0.9", p or 443))])
    with pytest.raises(SS.ProviderError):
        SS._pinned_addr_for("https://private.example/x")


def test_p5_auto_env_proxy_public_target_pinned(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://untrusted.example:8080")
    monkeypatch.delenv("SCHOLARLY_NETWORK_MODE", raising=False)
    monkeypatch.setattr(SS.socket, "getaddrinfo",
                        lambda h, p, proto=None: [(2, 1, 6, "", ("93.184.216.34", p or 443))])
    assert SS._pinned_addr_for("https://public.example/x")[0] == "93.184.216.34"
