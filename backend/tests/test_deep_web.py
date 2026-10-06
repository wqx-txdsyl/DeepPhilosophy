import json
import gzip
import threading
from email.message import Message
from types import SimpleNamespace

import pytest

import deep_web as web


@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://example.org/a", "http://localhost/a",
    "https://localhost./", "http://machine.local/", "https://user:secret@example.org/", "https://example.org:bad/",
    "https://example.org/\nHeader:bad"])
def test_invalid_and_local_urls_are_rejected_before_network(url, monkeypatch):
    monkeypatch.setattr(web.socket, "getaddrinfo", lambda *_a, **_k: pytest.fail("No DNS lookup allowed"))
    assert web.read_page({"url": url})["error"] in {"INVALID_WEB_URL", "PRIVATE_WEB_ADDRESS"}


def test_international_source_path_is_encoded_without_changing_existing_escapes():
    canonical, host, port = web.public_url("https://example.org/人格同一性?q=意识&lang=zh%2Dcn#章一")
    assert host == "example.org" and port == 443
    assert canonical == "https://example.org/%E4%BA%BA%E6%A0%BC%E5%90%8C%E4%B8%80%E6%80%A7?q=%E6%84%8F%E8%AF%86&lang=zh%2Dcn"
    assert web.public_url("https://example.org/wiki/Identity_(philosophy)")[0] == "https://example.org/wiki/Identity_%28philosophy%29"


@pytest.mark.parametrize("address", ["127.0.0.1", "10.0.0.1", "169.254.169.254", "0.0.0.0", "::1", "::ffff:127.0.0.1", "224.0.0.1", "198.18.1.1"])
def test_explicit_private_synthetic_and_special_ip_addresses_are_never_connected(address):
    host = f"[{address}]" if ":" in address else address
    with pytest.raises(web.WebReadError, match="PRIVATE_WEB_ADDRESS"):
        web.public_address(f"http://{host}/")


def dns(addresses):
    return [(web.socket.AF_INET, web.socket.SOCK_STREAM, 6, "", (ip, 443)) for ip in addresses]


def test_synthetic_dns_uses_validated_public_doh_destination_without_connecting_to_fake_ip(monkeypatch):
    monkeypatch.setattr(web.socket, "getaddrinfo", lambda *_a, **_k: dns(["198.18.0.5"]))
    calls = []
    monkeypatch.setattr(web, "_doh_addresses", lambda host: calls.append(host) or ["93.184.216.34"])
    address, mode = web.public_address("https://example.org/article")
    assert address == ("93.184.216.34", 443) and mode == "PUBLIC_DOH_PINNED"
    assert calls == ["example.org"]


def test_public_and_private_mixed_dns_does_not_bypass_protection(monkeypatch):
    monkeypatch.setattr(web.socket, "getaddrinfo", lambda *_a, **_k: dns(["93.184.216.34", "10.0.0.1"]))
    monkeypatch.setattr(web, "_doh_addresses", lambda *_a: pytest.fail("No fallback for private DNS"))
    with pytest.raises(web.WebReadError, match="PRIVATE_WEB_ADDRESS"):
        web.public_address("https://example.org/")


def test_doh_validates_every_returned_address_and_keeps_tls_verification(monkeypatch):
    seen = []
    class Connection:
        def __init__(self, host, timeout, context):
            assert host == "cloudflare-dns.com"
            assert context.check_hostname and context.verify_mode == web.ssl.CERT_REQUIRED
            seen.append(self)
        def request(self, method, path, headers):
            assert method == "GET" and "name=example.org" in path
            assert "Authorization" not in headers and "Cookie" not in headers
        def getresponse(self):
            return SimpleNamespace(status=200, read=lambda size: json.dumps({"Status": 0,
                "Answer": [{"type": 1, "data": "93.184.216.34"}, {"type": 1, "data": "127.0.0.1"}]}).encode())
        def close(self):
            self.closed = True
    monkeypatch.setattr(web.http.client, "HTTPSConnection", Connection)
    with pytest.raises(web.WebReadError, match="PRIVATE_WEB_ADDRESS"):
        web._doh_addresses("example.org")
    assert seen[0].closed


def test_https_socket_uses_checked_ip_and_original_hostname_for_tls(monkeypatch):
    monkeypatch.setattr(web, "public_address", lambda url: (("93.184.216.34", 443), "DIRECT_PINNED"))
    connections, tls_names = [], []
    fake_socket = SimpleNamespace(do_handshake=lambda: None)
    monkeypatch.setattr(web.socket, "create_connection", lambda address, timeout: connections.append(address) or fake_socket)
    handler = web._PinnedTLSHandler([])
    def do_open(cls, request, **kwargs):
        connection = cls("example.org", context=kwargs["context"])
        connection._context = SimpleNamespace(wrap_socket=lambda sock, server_hostname, **kwargs: tls_names.append(server_hostname) or sock)
        connection.connect()
        return connection
    monkeypatch.setattr(handler, "do_open", do_open)
    handler.https_open(web.urllib.request.Request("https://example.org/article"))
    assert connections == [("93.184.216.34", 443)] and tls_names == ["example.org"]


def test_total_deadline_closes_live_socket_and_rejects_late_connections():
    events = []
    sock = SimpleNamespace(shutdown=lambda how: events.append("shutdown"), close=lambda: events.append("close"))
    budget = web._ReadBudget()
    budget.track(sock)
    budget.expire()
    assert events == ["shutdown", "close"]
    with pytest.raises(web.WebReadError, match="WEB_FETCH_TIMEOUT"):
        budget.remaining()
    with pytest.raises(web.WebReadError, match="WEB_FETCH_TIMEOUT"):
        budget.track(sock)


def test_system_dns_wait_is_bounded_and_cannot_connect_after_timeout(monkeypatch):
    release = threading.Event()
    completed = threading.Event()
    def resolve(*_args, **_kwargs):
        release.wait(1)
        completed.set()
        return dns(["93.184.216.34"])
    monkeypatch.setattr(web.socket, "getaddrinfo", resolve)
    monkeypatch.setattr(web, "SOCKET_TIMEOUT", 0.01)
    monkeypatch.setattr(web.socket, "create_connection", lambda *_a, **_k: pytest.fail("Timed-out DNS cannot connect"))
    try:
        with pytest.raises(web.WebReadError, match="PUBLIC_DNS_TIMEOUT"):
            web.public_address("https://example.org/")
    finally:
        release.set()
        assert completed.wait(1)


def test_doh_connection_receives_the_same_total_budget(monkeypatch):
    seen = []
    class Connection:
        def __init__(self, host, timeout, context):
            self.host, self._context = host, context
        def request(self, *_args, **_kwargs):
            self.connect()
        def getresponse(self):
            return SimpleNamespace(status=200, read=lambda size: b'{"Status":0,"Answer":[{"type":1,"data":"93.184.216.34"}]}')
        def close(self):
            pass
    monkeypatch.setattr(web.http.client, "HTTPSConnection", Connection)
    monkeypatch.setattr(web, "_connect_tls", lambda connection, address, budget: seen.append((connection.host, address, budget)))
    with web._ReadBudget() as budget:
        assert web._doh_addresses("example.org", budget) == ["93.184.216.34"]
        assert seen == [("cloudflare-dns.com", ("1.1.1.1", 443), budget)]


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_redirect_body_is_closed_without_unbounded_drain(status):
    handler = web._Redirects()
    destinations = []
    handler.parent = SimpleNamespace(open=lambda request, timeout: destinations.append(request.full_url) or "followed")
    request = web.urllib.request.Request("https://example.org/start")
    request.timeout = 1
    headers = Message()
    headers["Location"] = "https://example.org/target"
    closed = []
    body = SimpleNamespace(close=lambda: closed.append(True),
                           read=lambda *_a: pytest.fail("Redirect bodies must not be drained"))
    assert getattr(handler, f"http_error_{status}")(request, body, status, "Redirect", headers) == "followed"
    assert closed == [True] and destinations == ["https://example.org/target"]


def test_redirects_recheck_target_and_enforce_per_request_limit(monkeypatch):
    handler = web._Redirects()
    req = web.urllib.request.Request("https://example.org/")
    for _ in range(4):
        assert handler.redirect_request(req, None, 302, "", {}, "https://elsewhere.example/")
    with pytest.raises(web.WebReadError, match="WEB_REDIRECT_LIMIT"):
        handler.redirect_request(req, None, 302, "", {}, "https://elsewhere.example/")
    with pytest.raises(web.WebReadError, match="PRIVATE_WEB_ADDRESS"):
        web._Redirects().redirect_request(req, None, 302, "", {}, "http://localhost/")
    monkeypatch.setattr(web.socket, "getaddrinfo", lambda *_a, **_k: dns(["10.0.0.1"]))
    with pytest.raises(web.WebReadError, match="PRIVATE_WEB_ADDRESS"):
        web._PinnedTLSHandler([]).https_open(web.urllib.request.Request("https://elsewhere.example/"))


def test_body_window_keeps_actual_offsets_and_does_not_duplicate_nested_paragraphs(monkeypatch):
    html = "<title>Source</title><nav>Navigation</nav><main><p>" + "Intro ß. " * 150 + "</p><blockquote><p>Unique target phrase explains a distinction.</p></blockquote><p>" + "Later paragraph. " * 300 + "</p></main>"
    monkeypatch.setattr(web, "fetch_page", lambda url: {"url": url, "body": html, "content_type": "text/html", "network_modes": ["DIRECT_PINNED"]})
    first = web.read_page({"url": "https://example.org/p", "focus": "Unique target phrase"})
    assert first["access_level"] == "WEB_PASSAGE_READ" and first["focus_found"]
    assert first["text"].count("Unique target phrase") == 1 and "Navigation" not in first["text"]
    assert first["end_offset"] - first["offset"] == len(first["text"])
    second = web.read_page({"url": "https://example.org/p", "offset": first["next_offset"]})
    assert second["offset"] == first["end_offset"] and second["content_hash"] == first["content_hash"]


def test_missing_focus_truncation_and_interstitial_are_not_silent_success(monkeypatch):
    page = {"url": "https://example.org/", "body": "a" * (web.MAX_TEXT_CHARS + 10), "content_type": "text/plain", "network_modes": []}
    monkeypatch.setattr(web, "fetch_page", lambda _url: page)
    result = web.read_page({"url": page["url"], "focus": "not present"})
    assert result["focus_found"] is False and result["document_truncated"] is True
    assert web.read_page({"url": page["url"], "offset": web.MAX_TEXT_CHARS})["error"] == "WEB_OFFSET_OUT_OF_RANGE"
    page.update(content_type="text/html", body="<title>Just a moment</title><form id='challenge-form'>" + "Wait " * 30 + "</form>")
    assert web.read_page({"url": page["url"]})["error"] == "WEB_ACCESS_CHALLENGE"


def test_general_registry_adds_read_mode_without_mutating_persona_schema(monkeypatch):
    import engine_langgraph as engine
    from routes import agent_tools_retrieval as legacy
    original = legacy.TOOLS["websearch"]
    original_schema = json.dumps(original["parameters"], sort_keys=True)
    general = {tool.name: tool for tool in engine._build_tools(general=True)}["websearch"]
    assert "url" in general.args
    assert "url" not in original["parameters"]["properties"]
    monkeypatch.setattr(web, "read_page", lambda args: {"mode": "read", "text": "actual text", "url": args["url"]})
    assert general.func(url="https://example.org/")["mode"] == "read"
    assert general.func(query="query", url="https://example.org/")["error"] == "AMBIGUOUS_WEB_REQUEST"
    assert general.func()["error"] == "MISSING_WEB_REQUEST"
    assert json.dumps(original["parameters"], sort_keys=True) == original_schema


def test_web_read_text_and_url_survive_model_context_limit():
    from deep_tool_context import tool_context
    result = {"mode": "read", "text": "正文。" * 800, "url": "https://example.org/" + "a" * 2000,
              "next_offset": 2400, "access_level": "WEB_PASSAGE_READ"}
    content, metadata = tool_context("websearch", result, "general")
    assert json.loads(content) == result and metadata["status"] == "complete"


def test_fetch_enforces_decoded_size_and_rejects_unsupported_formats(monkeypatch):
    class Response:
        def __init__(self, data, content_type="text/html", encoding="identity"):
            self.data = data
            self.headers = Message()
            self.headers["Content-Type"] = content_type
            self.headers["Content-Encoding"] = encoding
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            pass
        def geturl(self):
            return "https://example.org/"
        def read1(self, length):
            part, self.data = self.data[:length], self.data[length:]
            return part
    current = [Response(gzip.compress(b"x" * (web.MAX_BYTES + 1)), encoding="gzip")]
    monkeypatch.setattr(web.urllib.request, "build_opener", lambda *handlers: SimpleNamespace(open=lambda *a, **k: current[0]))
    with pytest.raises(web.WebReadError, match="WEB_RESPONSE_TOO_LARGE"):
        web.fetch_page("https://example.org/")
    current[0] = Response(b"%PDF", content_type="application/pdf")
    with pytest.raises(web.WebReadError, match="UNSUPPORTED_WEB_FORMAT"):
        web.fetch_page("https://example.org/")
    current[0] = Response(gzip.compress(b"<p>A genuinely returned public passage.</p>"), encoding="gzip")
    assert b"public passage" in web.fetch_page("https://example.org/")["body"]


def test_html_declared_charset_is_respected_in_actual_extraction():
    body = ('<meta charset="windows-1252"><title>Identity</title><main><p>' + 'Über die Identität. ' * 15 + '</p></main>').encode('cp1252')
    result = web.extract_page({"body": body, "url": "https://example.org/", "content_type": "text/html"})
    assert 'Über die Identität.' in result["text"] and '\ufffd' not in result["text"]
