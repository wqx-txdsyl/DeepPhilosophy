# -*- coding: utf-8 -*-
"""O7-C — Scholarly secondary-source retrieval core（scholarly_sources.py）。

原则（O7-C 任务书）:
  - PAPER_EXISTS != PAPER_READ; FULL_TEXT_AVAILABLE != FULL_TEXT_READ
  - bibliographic existence 只来自 retrieved record, 绝不模型记忆/LLM 补全
  - access_level 四态状态机只由实际证据驱动:
      METADATA_ONLY → ABSTRACT_AVAILABLE → FULL_TEXT_AVAILABLE → FULL_TEXT_READ
  - retrieval failure != scholarly absence（provider 错误不转为「没有文献」）
  - 仅合法访问: open access / public domain / 官方 metadata-abstract;
    禁 paywall/credential bypass/Sci-Hub/登录态抓取
  - SSRF 边界: 只允许访问已检索 provider record 中的 https/http source URL,
    禁 localhost/私网/file/ftp/169.254

Providers: Crossref + OpenAlex（官方公开 API, 无鉴权; feasibility audit 见
docs/PHIAGENT_O7C_SCHOLARLY_RETRIEVAL.md）。SEP/PhilPapers = NOT_IMPLEMENTED。
"""
import hashlib
import http.client
import ipaddress
import json
import os
import re
import socket
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_PATH = os.path.join(ROOT, "backend", "data", "scholarly_cache.json")

# RP2 §4 Option B: 单一真实 socket timeout（作用于实际 connection 的全部
# blocking 操作）; 不做「probe 一条连接、声称约束另一条」的假分离。
NETWORK_SOCKET_TIMEOUT = 20
MAX_REDIRECTS = 4
MAX_BYTES = 5 * 1024 * 1024   # full text 不无界下载
USER_AGENT = "DeepPhilosophy-PhiAgent/0.7 (scholarly metadata; contact: site-admin)"

SCHEMA_VERSION = "o7c-1"

# ── 网络信任边界（Final Gate Patch §C-E）──
# DIRECT_PINNED: 直连 + 逐请求 IP pin; 198.18.0.0/15 按 reserved 拒绝
# TRUSTED_PROXY: 用户显式信任的代理/TUN（DNS 解析与出网边界委托给代理;
#                此时 fake-IP 段 198.18/15 是代理分配的映射地址, 允许）
# AUTO(默认): 检测到系统代理也【不】静默信任——按 DIRECT_PINNED 安全直连处理
def _network_mode():
    return os.environ.get("SCHOLARLY_NETWORK_MODE", "AUTO").upper()

def _fake_ip_allowed():
    return _network_mode() == "TRUSTED_PROXY"

def dns_rebinding_mode():
    return ("TRUSTED_PROXY_DELEGATED" if _network_mode() == "TRUSTED_PROXY"
            else "DIRECT_IP_PINNED")
ACCESS_LEVELS = ("METADATA_ONLY", "ABSTRACT_AVAILABLE", "FULL_TEXT_AVAILABLE",
                 "FULL_TEXT_READ")
_LEVEL_ORDER = {lv: i for i, lv in enumerate(ACCESS_LEVELS)}

# ── 网络安全边界（§50/§51）────────────────────────────────────────
_PRIVATE = set()


def _url_guard(url):
    """SSRF 边界: https/http only; 域名解析后禁私网/环回/链路本地。"""
    try:
        u = urllib.parse.urlsplit(url)
    except ValueError:
        return False, "unparsable url"
    if u.scheme not in ("https", "http"):
        return False, f"scheme {u.scheme!r} not allowed"
    host = u.hostname or ""
    if not host:
        return False, "no host"
    if host in ("localhost",) or host.endswith(".localhost") or host.endswith(".local"):
        return False, "local host"
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError as e:
        return False, f"dns failure: {e}"
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip in ipaddress.ip_network("198.18.0.0/15"):
            if _fake_ip_allowed():
                continue   # 仅显式 TRUSTED_PROXY/TUN fake-IP 模式允许该映射段
            return False, "reserved ip 198.18.0.0/15（非 trusted fake-IP 模式默认拒绝）"
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return False, f"private/reserved ip {ip}"
    return True, "ok"


class ProviderError(Exception):
    def __init__(self, kind, detail=""):
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail


class _PinnedHTTP(http.client.HTTPConnection):
    """DNS-pinned 连接: 实际 connect 目标 = SSRF guard 校验过的公网地址。

    覆盖 _create_connection（HTTP/HTTPS 共用入口）→ 消除 guard 与真实连接
    之间的 DNS TOCTOU（RP2 §7 Option A: pin one validated public IP）。"""
    _pinned_addr = None

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        if self._pinned_addr is not None:
            addr = self._pinned_addr

            def _cc(host, port, timeout=None, source_address=None, sockopts=None):
                return socket.create_connection(addr, timeout=NETWORK_SOCKET_TIMEOUT)

            self._create_connection = _cc
        self.timeout = NETWORK_SOCKET_TIMEOUT


class _PinnedHTTPS(_PinnedHTTP, http.client.HTTPSConnection):
    pass


class _GuardedRedirectHandler(urllib.request.HTTPRedirectHandler):
    """RP2 §5: redirect 计数为 handler 实例级（每请求新建 opener/handler）,
    并发请求不共享 hop counter; 每一跳 target 过 SSRF guard。"""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.hops = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if self.hops >= MAX_REDIRECTS:
            raise ProviderError("REDIRECT_LIMIT", f">{MAX_REDIRECTS} redirects: {newurl}")
        ok, why = _url_guard(newurl)
        if not ok:
            raise ProviderError("URL_BLOCKED", f"redirect target {why}: {newurl}")
        self.hops += 1
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _pinned_addr_for(url):
    """解析并校验目标地址; 返回第一个通过 guard 的 (family, sockaddr) 或抛错。"""
    u = urllib.parse.urlsplit(url)
    host, port = u.hostname, u.port or (443 if u.scheme == "https" else 80)
    infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    fake_ip = None
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip in ipaddress.ip_network("198.18.0.0/15"):
            # 仅显式 TRUSTED_PROXY 模式: 该段是本机代理 TUN 分配的映射地址
            if not _fake_ip_allowed():
                raise ProviderError("URL_BLOCKED",
                                    f"reserved ip {ip}（非 trusted fake-IP 模式）")
            if fake_ip is None:
                fake_ip = info[4]
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ProviderError("URL_BLOCKED", f"private/reserved ip {ip}")
        return info[4]
    if fake_ip is not None:
        return fake_ip
    raise ProviderError("URL_BLOCKED", f"no valid address for {host}")


class _PinnedHTTPHandler(urllib.request.HTTPHandler):
    """逐请求/逐跳 pin: do_open 时按当前 req 的目标 URL 重新 guard+resolve+pin
    （redirect 到 host-B 时第二跳 pin host-B, 不是初始 host-A）。"""

    def do_open(self, http_class, req, **kw):
        class _C(_PinnedHTTP):
            _pinned_addr = _pinned_addr_for(req.full_url)
        return super().do_open(_C, req, **kw)


class _PinnedHTTPSHandler(urllib.request.HTTPSHandler):
    def do_open(self, http_class, req, **kw):
        class _C(_PinnedHTTPS):
            _pinned_addr = _pinned_addr_for(req.full_url)
        return super().do_open(_C, req, **kw)


class _Resp:
    __slots__ = ("status", "body", "final_url", "content_type", "redirect_count")


def _build_network_opener():
    """薄 transport helper（Patch 2 §2）: 按显式网络模式构造 opener。

    - TRUSTED_PROXY: 允许系统代理配置（DNS/出网边界委托, DELEGATED 如实上报）
    - DIRECT_PINNED / AUTO: ProxyHandler({}) 显式禁用环境代理——
      build_opener 默认自动装载 env proxy, 不显式替换时 direct 路径会被悄悄接管。
    """
    rh = _GuardedRedirectHandler()
    if _network_mode() == "TRUSTED_PROXY":
        return urllib.request.build_opener(rh)
    hh = _PinnedHTTPHandler()
    hs = _PinnedHTTPSHandler()
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}), hs, hh, rh)


def _http_get(url, accept="application/json"):
    """带硬上限与完整 provenance 的 GET。

    返回 _Resp(status, body, final_url, content_type, redirect_count)。
    timeout 语义（RP2 §4 Option B）: NETWORK_SOCKET_TIMEOUT=20 作用于实际
    connection/socket 的全部 blocking 操作（connect+read 同一 socket）。
    DNS pinning（RP2 §7）: guard 校验过的地址直接作为 connect 目标。"""
    ok, why = _url_guard(url)
    if not ok:
        raise ProviderError("URL_BLOCKED", why)
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT, "Accept": accept,
        "Accept-Encoding": "identity"})
    opener = _build_network_opener()
    rh = next((h for h in opener.handlers
               if isinstance(h, _GuardedRedirectHandler)), None)
    with opener.open(req, timeout=NETWORK_SOCKET_TIMEOUT) as r:
        data = r.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ProviderError("RESPONSE_TOO_LARGE", url)
        resp = _Resp()
        resp.status = r.status
        resp.body = data
        resp.final_url = r.geturl()
        resp.content_type = (r.headers.get("Content-Type") or "").split(";")[0].strip()
        resp.redirect_count = rh.hops
        return resp



def _get_json(url):
    try:
        resp = _http_get(url)
    except ProviderError:
        raise                       # REDIRECT_LIMIT / URL_BLOCKED 原样透传
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise ProviderError("PROVIDER_RATE_LIMIT", str(e.code))
        raise ProviderError("PROVIDER_UNAVAILABLE", f"http {e.code}")
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        if "timed out" in str(reason).lower():
            raise ProviderError("PROVIDER_TIMEOUT", str(reason))
        raise ProviderError("PROVIDER_UNAVAILABLE", str(reason))
    except socket.timeout:
        raise ProviderError("PROVIDER_TIMEOUT", url)
    try:
        return json.loads(resp.body.decode("utf-8", "replace"))
    except json.JSONDecodeError:
        raise ProviderError("MALFORMED_PROVIDER_RESPONSE", url)


# ── DOI 归一（§10）──────────────────────────────────────────────
def normalize_doi(raw):
    if not raw or not isinstance(raw, str):
        return None
    m = re.search(r"(10\.\d{4,9}/\S+)", raw.strip(), re.I)
    if not m:
        return None
    doi = m.group(1).rstrip(".,;)")
    return doi.lower()


# ── Provider adapters ──────────────────────────────────────────
PUB_TYPE_MAP_CROSSREF = {
    "journal-article": "JOURNAL_ARTICLE", "book": "BOOK",
    "book-chapter": "BOOK_CHAPTER", "proceedings-article": "PROCEEDINGS",
    "dissertation": "DISSERTATION", "report": "OTHER", "posted-content": "OTHER",
}
PUB_TYPE_MAP_OPENALEX = {
    "article": "JOURNAL_ARTICLE", "book": "BOOK", "book-chapter": "BOOK_CHAPTER",
    "dissertation": "DISSERTATION", "proceedings-article": "PROCEEDINGS",
}


def _fingerprint(title, first_author, year, venue):
    """§9 bibliographic fingerprint（无 DOI 时）; 含 year+venue 防同题异刊合并。"""
    norm = re.sub(r"\W+", " ", (title or "").lower()).strip()
    key = f"{norm}|{(first_author or '').lower()}|{year or ''}|{(venue or '').lower()}"
    return "fp-" + hashlib.sha256(key.encode()).hexdigest()[:16]


def search_crossref(query, limit=8, year_from=None, year_to=None):
    q = urllib.parse.quote(query)
    url = (f"https://api.crossref.org/works?query.bibliographic={q}"
           f"&rows={min(limit, 20)}&select=title,author,DOI,issued,container-title,"
           f"type,is-referenced-by-count,abstract,subject")
    if year_from or year_to:
        lo = year_from or 1900
        hi = year_to or 2100
        url += f"&filter=from-pub-date:{lo}-01-01,until-pub-date:{hi}-12-31"
    data = _get_json(url)
    out = []
    for it in data.get("message", {}).get("items", []):
        year = None
        try:
            year = it.get("issued", {}).get("date-parts", [[None]])[0][0]
        except (IndexError, TypeError, KeyError):
            pass
        authors = [{"name": " ".join(filter(None, [a.get("given"), a.get("family")])).strip()
                    or a.get("name", ""), "orcid": a.get("ORCID")}
                   for a in it.get("author", [])] or None
        t = (it.get("title") or [""])[0] or None
        venue = (it.get("container-title") or [None])[0]
        rec = {
            "title": t,
            "authors": authors,
            "publication_year": year,
            "container_title": venue,
            "publication_type": PUB_TYPE_MAP_CROSSREF.get(it.get("type"), "OTHER"),
            "doi": normalize_doi(it.get("DOI")),
            "stable_urls": (["https://doi.org/" + it["DOI"]] if it.get("DOI") else []),
            "abstract_text": _strip_jref(it.get("abstract")) if it.get("abstract") else None,
            "provider": "crossref",
            "provider_record_id": it.get("DOI") or None,
            "cited_by": it.get("is-referenced-by-count"),
        }
        out.append(rec)
    return out


_JREF = re.compile(r"<jats?:[^>]+>")

def _strip_jref(s):
    return re.sub(r"\s+", " ", _JREF.sub("", s)).strip() or None


def _inverted_to_text(inv):
    if not inv:
        return None
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos)) or None


def search_openalex(query, limit=8, year_from=None, year_to=None):
    q = urllib.parse.quote(query)
    # mailto 礼貌池（OpenAlex 文档: 提供 contact 进入 polite pool, 限流显著放宽）
    url = (f"https://api.openalex.org/works?search={q}&per-page={min(limit, 20)}"
           f"&mailto=deepphilosophy.agent@outlook.com"
           f"&select=id,doi,title,publication_year,type,open_access,primary_location,"
           f"authorships,abstract_inverted_index,cited_by_count")
    if year_from:
        url += f"&filter=from_publication_date:{year_from}-01-01"
    if year_to:
        url += (("&filter=" if "filter=" not in url else ",")
                + f"to_publication_date:{year_to}-12-31")
    data = _get_json(url)
    out = []
    for it in data.get("results", []):
        loc = it.get("primary_location") or {}
        src = (loc.get("source") or {})
        oa = it.get("open_access") or {}
        rec = {
            "title": it.get("title") or it.get("display_name"),
            "authors": [{"name": a.get("author", {}).get("display_name", ""),
                         "orcid": a.get("author", {}).get("orcid")}
                        for a in it.get("authorships", [])][:12] or None,
            "publication_year": it.get("publication_year"),
            "container_title": src.get("display_name"),
            "publication_type": PUB_TYPE_MAP_OPENALEX.get(it.get("type"), "OTHER"),
            "doi": normalize_doi(it.get("doi")),
            "stable_urls": ([it["doi"]] if it.get("doi") else [])
                           + ([loc["landing_page_url"]] if loc.get("landing_page_url") else []),
            "abstract_inverted_index": it.get("abstract_inverted_index"),
            "abstract_source": "OPENALEX_INVERTED_INDEX" if it.get("abstract_inverted_index") else None,
            "open_access": oa,
            "oa_pdf_url": loc.get("pdf_url") or oa.get("oa_url"),
            "oa_candidate_kind": ("DIRECT_PDF" if loc.get("pdf_url")
                                  else "OA_LOCATION"),
            "provider": "openalex",
            "provider_record_id": (it.get("id") or "").rsplit("/", 1)[-1] or None,
            "cited_by": it.get("cited_by_count"),
        }
        out.append(rec)
    return out


# ── Canonical record / dedup（§8/§9/§11）───────────────────────────
def canonical_source_record_id(provider_records):
    """DOI normalized 优先; 否则 provider canonical ID; 再无 → fingerprint。"""
    for r in provider_records:
        if r.get("doi"):
            return "doi:" + r["doi"]
    for r in provider_records:
        if r.get("provider_record_id"):
            return f"{r['provider']}:{r['provider_record_id']}"
    r0 = provider_records[0]
    return _fingerprint(r0.get("title"),
                        (r0.get("authors") or [{}])[0].get("name"),
                        r0.get("publication_year"), r0.get("container_title"))


def merge_records(records):
    """跨 provider 去重: 同 DOI → 合并为一个 canonical record（多 provider_records）;
    异 DOI 不合并; 无 DOI 时仅当 title+author+year+venue 机械一致才合并。"""
    by_doi, no_doi = {}, []
    for r in records:
        if r.get("doi"):
            by_doi.setdefault(r["doi"], []).append(r)
        else:
            no_doi.append(r)
    canon = []
    for doi, rs in by_doi.items():
        canon.append(_mk_canonical(rs))
    for r in no_doi:
        placed = False
        for c in canon:
            # 无 DOI 与有 DOI 记录: 仅机械全一致才并（MERGE 由 DOI 主导, 此处保守不并）
            _ = c
            placed = False
        if not placed:
            canon.append(_mk_canonical([r]))
    # 无 DOI 之间的机械合并: fingerprint 相同
    merged_nodoi = {}
    for c in canon:
        if c["source_record_id"].startswith("fp-"):
            merged_nodoi.setdefault(c["source_record_id"], []).append(c)
    out = []
    for sid, cs in merged_nodoi.items():
        rs = [r for c in cs for r in c["provider_records"]]
        out.append(_mk_canonical(rs))
    out += [c for c in canon if not c["source_record_id"].startswith("fp-")]
    return out


def _mk_canonical(provider_records):
    sid = canonical_source_record_id(provider_records)
    rec = {"source_record_id": sid, "schema_version": SCHEMA_VERSION,
           "title": None, "authors": None, "publication_year": None,
           "container_title": None, "publication_type": "OTHER",
           "identifiers": {"doi": None, "provider_ids": []},
           "stable_urls": [], "provider_records": provider_records,
           "access": {"level": "METADATA_ONLY", "evidence": "provider metadata only",
                      "checked_at": None, "full_text_url": None, "content_hash": None},
           "abstract": {"text": None, "source": None, "hash": None},
           "provenance": {"providers": sorted({r["provider"] for r in provider_records}),
                          "field_sources": {}},
           "conflicts": [], "philosophical_role": "UNKNOWN",
           "peer_review_status": "UNVERIFIED"}
    # 字段: 多 provider 一致取值; 异值 → conflict 保留（§12）
    def set_field(field):
        vals = []
        for r in provider_records:
            v = r.get(field if field != "doi" else "doi")
            if v not in (None, "", []):
                vals.append((v, r["provider"]))
        if not vals:
            return
        distinct = []
        for v, p in vals:
            if v not in [d for d, _ in distinct]:
                distinct.append((v, p))
        if len(distinct) == 1:
            rec[field if field != "doi" else "_doi"] = distinct[0][0] \
                if field != "doi" else distinct[0][0]
            if field == "doi":
                rec["identifiers"]["doi"] = distinct[0][0]
                rec["identifiers"]["doi_verified"] = True  # provider record 明确绑定
            rec["provenance"]["field_sources"][field] = distinct[0][1]
        else:
            rec["conflicts"].append({
                "field": field,
                "candidate_values": [v for v, _ in distinct],
                "providers": [p for _, p in distinct],
                "resolution_status": "CONFLICT_UNRESOLVED"})
            rec[field] = None if field != "doi" else rec["identifiers"]["doi"]

    for f in ("title", "authors", "publication_year", "container_title",
              "publication_type", "doi"):
        set_field(f)
    for r in provider_records:
        pid = r.get("provider_record_id")
        if pid:
            rec["identifiers"]["provider_ids"].append(f"{r['provider']}:{pid}")
        rec["stable_urls"].extend(u for u in r.get("stable_urls", []) if u)
    rec["stable_urls"] = list(dict.fromkeys(rec["stable_urls"]))[:6]
    # abstract: 取第一个有值的 provider 版本（保留 provider-specific, 不拼接 §55）
    for r in provider_records:
        if r.get("abstract_text"):
            rec["abstract"].update(
                {"text": r["abstract_text"], "source": f"{r['provider']}_METADATA"})
            break
        if r.get("abstract_inverted_index"):
            txt = _inverted_to_text(r["abstract_inverted_index"])
            if txt:
                rec["abstract"].update({"text": txt, "source": "OPENALEX_INVERTED_INDEX"})
                break
    if rec["abstract"]["text"]:
        rec["abstract"]["hash"] = hashlib.sha256(
            rec["abstract"]["text"].encode()).hexdigest()
        rec["access"] = {"level": "ABSTRACT_AVAILABLE",
                         "evidence": f"abstract from {rec['abstract']['source']}",
                         "checked_at": int(time.time()),
                         "full_text_url": None, "content_hash": None}
    # O7-C RP1 §1: provider OA URL 只是机械候选, 不自动升级 access level
    #   provider says OA != URL verified reachable
    rec["full_text_candidates"] = [
        {"url": r["oa_pdf_url"], "provider": r["provider"],
         "access_claim": "OPEN_ACCESS",
         "candidate_kind": r.get("oa_candidate_kind") or "OA_LOCATION"}
        for r in provider_records
        if (r.get("oa_pdf_url") or "").startswith(("https://", "http://"))]
    return rec


# ── Access state machine（§13-§18）───────────────────────────────
def _promote_access(rec, candidate_level, evidence, url=None, chash=None, extra=None):
    """RP2 §1: 单调晋升——new = max(current, candidate); 任何路径不得降级。"""
    cur = _LEVEL_ORDER[rec["access"]["level"]]
    cand = _LEVEL_ORDER[candidate_level]
    if cand < cur:
        return  # 历史证据仍然成立, 不因后续失败撤销（RP2 M1-M3）
    rec["access"] = {"level": candidate_level if cand >= cur else rec["access"]["level"],
                     "evidence": evidence,
                     "checked_at": int(time.time()),
                     "full_text_url": url, "content_hash": chash}
    if extra:
        rec["access"].update(extra)


def get_evidence(rec, requested_access):
    """RP2: 单调状态机 + candidate_kind READ 真实性 + 逐候选尝试记账。

    READ 只可能来自 DIRECT_PDF: HTTP 2xx + PDF magic + 解析出正文。
    HTML OA_LOCATION 至多 FULL_TEXT_AVAILABLE（landing page ≠ 论文正文）。"""
    before = rec["access"]["level"]
    info = {"source_record_id": rec["source_record_id"],
            "access_level_before": before,
            "access_level_after": before,          # 单调: 只升不降
            "returned_evidence_level": None,
            "full_text_status": None, "evidence_passages": [],
            "passage_locators": [], "source_url": None, "content_hash": None,
            "access_notes": "", "full_text_attempts": []}
    if rec["abstract"]["text"]:
        info["abstract"] = dict(rec["abstract"])

    if requested_access == "ABSTRACT":
        if rec["abstract"]["text"]:
            info["returned_evidence_level"] = "ABSTRACT_AVAILABLE"
            info["access_level_after"] = max(
                before, "ABSTRACT_AVAILABLE", key=lambda l: _LEVEL_ORDER[l])
            info["access_notes"] = "abstract 返回; 状态字段单调不降"
            return rec, info
        # O7-D RP1 §8: 本地 registry 持久化 abstract 回退
        if rec.get("ingest") is not None:
            try:
                import scholarly_registry as _SR
                evs = [e for e in _SR.evidence_for(rec["source_record_id"])
                       if e["evidence_type"] == "ABSTRACT"]
            except Exception:
                evs = []
            if evs:
                e = evs[0]
                info["abstract"] = {"text": e["text"], "source": e.get("abstract_source"),
                                    "hash": e.get("abstract_hash")}
                info["returned_evidence_level"] = "ABSTRACT_AVAILABLE"
                info["access_level_after"] = max(
                    before, "ABSTRACT_AVAILABLE", key=lambda l: _LEVEL_ORDER[l])
                info["access_notes"] = ("持久化 abstract 返回（evidence_origin="
                                        "ABSTRACT_METADATA, 本地 registry）")
                return rec, info
        info["access_notes"] = ("abstract 未取得: 不得凭 title 推断论文内容; "
                                "状态保持不变")
        return rec, info

    # O7-D RP1 §8-9: 本地 registry 记录的持久证据回退（历史验证读 ≠ 当前读）
    if rec.get("ingest") is not None:
        try:
            import scholarly_registry as _SR
            evs = _SR.evidence_for(rec["source_record_id"])
        except Exception:
            evs = []
        passages = [e for e in evs if e["evidence_type"] == "FULLTEXT_PASSAGE"]
        if (rec["ingest"].get("access_level_at_ingest") == "FULL_TEXT_READ"
                and passages):
            info.update({
                "access_level_after": rec["access"]["level"],   # 不虚构当前 FULL_TEXT_READ
                "historical_evidence_level": "FULL_TEXT_READ",
                "full_text_status": "PERSISTED_VERIFIED_READ",
                "evidence_passages": [
                    {"passage_id": e["evidence_id"], "locator": None,
                     "text": e["text"], "page": None} for e in passages[:5]],
                "access_notes": ("此前验证读取并持久化的证据节选（evidence_origin="
                                 "PERSISTED_VERIFIED_READ）; 本轮未重新获取全文, "
                                 "不声称当前 URL 仍可访问")})
            for e in passages[:5]:
                info.setdefault("_evidence_origin_items", []).append(
                    {"evidence_id": e["evidence_id"],
                     "evidence_origin": "PERSISTED_VERIFIED_READ"})
            return rec, info

    cands = rec.get("full_text_candidates") or []
    if not cands:
        info["access_notes"] = ("无 OA 全文候选; DOI landing page 不构成全文可用")
        return rec, info
    last_err = None
    for cand in cands[:3]:
        url = cand["url"]
        info["source_url"] = url
        attempt = {"candidate_url": url,
                   "candidate_kind": cand.get("candidate_kind"),
                   "result": None, "http_status": None}
        try:
            resp = _http_get(url, accept="application/pdf,text/html,*/*")
        except ProviderError as e:
            last_err = e.kind
            attempt["result"] = "BLOCKED" if e.kind == "URL_BLOCKED" else "HTTP_FAILURE"
            info["full_text_attempts"].append(attempt)
            continue
        except urllib.error.HTTPError as e:
            last_err = f"HTTP_{e.code}"
            attempt.update(result="HTTP_FAILURE", http_status=e.code)
            info["full_text_attempts"].append(attempt)
            continue
        except (urllib.error.URLError, OSError):
            last_err = "NETWORK"
            attempt["result"] = "HTTP_FAILURE"
            info["full_text_attempts"].append(attempt)
            continue
        attempt["http_status"] = resp.status
        # Final Gate Patch §A: 只有 body 以 %PDF 魔数开头才尝试 PDF 解析;
        # Content-Type/URL 命名只是提示, 不构成 body 证明（document body beats naming）
        body_is_pdf = resp.body[:4] == b"%PDF"
        text = _extract_text(resp.body, url) if body_is_pdf else None
        if (body_is_pdf and text and len(text.strip()) >= 200
                and cand.get("candidate_kind") == "DIRECT_PDF"):
            # READ = DIRECT_PDF + %PDF body 签名 + 解析成功（缺一不可）
            chash = hashlib.sha256(resp.body).hexdigest()
            _promote_access(rec, "FULL_TEXT_READ", "verified PDF body parsed",
                            url=resp.final_url, chash=chash,
                            extra={"content_length": len(text),
                                   "parser": "pdftotext",
                                   "content_type": resp.content_type,
                                   "redirect_count": resp.redirect_count,
                                   "candidate_kind": "DIRECT_PDF",
                                   "verified_document_kind": "PDF",
                                   "body_signature_verified": True})
            info.update({"access_level_after": rec["access"]["level"],
                         "full_text_status": "READ",
                         "content_hash": chash,
                         "evidence_passages": _top_passages(text, None),
                         "access_notes": "verified PDF body 已解析; 返回节选段落"})
            attempt["result"] = "READ"
            attempt["body_signature_verified"] = True
            info["full_text_attempts"].append(attempt)
            return rec, info
        # PDF 解析失败 或 HTML OA_LOCATION → 至多 AVAILABLE（RP2 §10）
        _promote_access(rec, "FULL_TEXT_AVAILABLE",
                        f"verified retrievable (HTTP {resp.status}, "
                        f"{resp.content_type}, final={resp.final_url}, "
                        f"redirects={resp.redirect_count})",
                        url=resp.final_url,
                        extra={"content_type": resp.content_type,
                               "final_url": resp.final_url,
                               "redirect_count": resp.redirect_count,
                               "candidate_kind": cand.get("candidate_kind")})
        info.update({"access_level_after": rec["access"]["level"],
                     "full_text_status": "AVAILABLE_ONLY",
                     "access_notes": ("HTML OA_LOCATION/PDF body 未验证 → AVAILABLE"
                                      "（landing page 不冒充论文正文）")})
        attempt["result"] = "AVAILABLE_ONLY"
        attempt["pdf_parse_failed"] = bool(cand.get("candidate_kind") == "DIRECT_PDF"
                                           and body_is_pdf)
        info["full_text_attempts"].append(attempt)
        return rec, info
    info["full_text_status"] = f"FETCH_FAILED:{last_err}"
    info["access_notes"] = (f"OA 候选全部失败（{last_err}）; 状态保持 {before}, "
                            "不虚报全文可用")
    return rec, info



def _extract_text(data, url):
    if url.lower().endswith(".pdf") or data[:4] == b"%PDF":
        try:
            return _pdf_text(data)
        except Exception:
            return None
    try:
        html = data.decode("utf-8", "replace")
    except Exception:
        return None
    html = re.sub(r"(?is)<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", html)
    txt = re.sub(r"(?s)<[^>]+>", " ", html)
    return re.sub(r"[ \t]+", " ", txt)


def _pdf_text(data):
    import subprocess, tempfile, shutil
    if not shutil.which("pdftotext"):
        return None
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(data)
        p = f.name
    try:
        r = subprocess.run(["pdftotext", "-q", p, "-"], capture_output=True, timeout=60)
        return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None
    finally:
        os.unlink(p)


def _top_passages(text, query_terms, n=3):
    """机械节选: 开头/中部/结尾各一段（无 query 时）; 不造页码。"""
    paras = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 200]
    if not paras:
        return []
    pick = [paras[0]]
    if len(paras) > 2:
        pick.append(paras[len(paras) // 2])
        pick.append(paras[-1])
    out = []
    for i, p in enumerate(pick[:n]):
        out.append({"passage_id": f"p{i}", "locator": None,
                    "text": p[:900], "page": None})   # HTML/PDF 未保页号 → page=null
    return out


# ── 缓存（§29 机械优化）─────────────────────────────────────────
_cache = None

def _load_cache():
    global _cache
    if _cache is None:
        try:
            _cache = json.load(open(CACHE_PATH, encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            _cache = {"searches": {}, "records": {}}
    return _cache


def _save_cache():
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        json.dump(_cache, open(CACHE_PATH, "w", encoding="utf-8"), ensure_ascii=False)
    except OSError:
        pass


def _local_results(q, limit):
    """O7-D §23-25: LOCAL_CURATED provider（registry, 非 authority）。
    失败静默降级为无本地结果（registry 缺失≠错误, 只是未构建）。"""
    try:
        import scholarly_registry as SR
        return SR.search_local(q, limit=limit)
    except Exception:
        return []


def _live_origin(r):
    ps = {p for p in r.get("provenance", {}).get("providers", [])}
    if len(ps) >= 2:
        return "LIVE_COMBINED"
    if "crossref" in ps:
        return "LIVE_CROSSREF"
    if "openalex" in ps:
        return "LIVE_OPENALEX"
    return "LIVE"


def _dedup_local_live(local, live):
    """同 source_record_id / 同 DOI → 单 canonical; retrieval_origin 双真值
    （local+live 命中 → LOCAL_CURATED+LIVE）; bibliographic source provenance 不丢。"""
    out = list(local)
    index = {r["source_record_id"]: r for r in local}
    seen_doi = {r["identifiers"].get("doi") for r in local if r["identifiers"].get("doi")}
    for r in live:
        doi = r["identifiers"].get("doi")
        if r["source_record_id"] in index or (doi and doi in seen_doi):
            sid = r["source_record_id"] if r["source_record_id"] in index else None
            if sid is None:   # 同 DOI 异 id: 找 local 中同 doi 的
                sid = next(x["source_record_id"] for x in local
                           if x["identifiers"].get("doi") == doi)
            index[sid]["retrieval_origin"] = "LOCAL_CURATED+LIVE"
            continue
        r = dict(r, retrieval_origin=_live_origin(r))
        out.append(r)
        index[r["source_record_id"]] = r
        if doi:
            seen_doi.add(doi)
    return out


def search_scholarship(query, philosopher=None, work=None, year_from=None,
                       year_to=None, limit=8):
    """主入口: LOCAL_CURATED + Crossref + OpenAlex → canonical 去重。

    O7-D §26-27 离线语义: 双 live provider 失败而本地有结果时如实标注
    「外部 provider 当前失败; 结果来自本地 registry」, 不冒充实时检索。"""
    q = " ".join(filter(None, [philosopher, work, query])).strip()
    key = json.dumps([q, year_from, year_to, limit], ensure_ascii=False)
    cache = _load_cache()
    if key in cache["searches"]:
        return cache["searches"][key]
    results, errors = [], []
    live_ok = []
    for name, fn in (("crossref", search_crossref), ("openalex", search_openalex)):
        try:
            results.extend(fn(q, limit=limit, year_from=year_from, year_to=year_to))
            live_ok.append(name)
        except ProviderError as e:
            errors.append({"provider": name, "error": e.kind, "detail": e.detail})
    canon = merge_records(results)
    canon.sort(key=lambda r: -(r.get("provider_records", [{}])[0].get("cited_by") or 0))
    local = _local_results(q, limit)
    merged = _dedup_local_live(local, canon)[:limit]
    out = {"query": q, "results": merged,
           "providers_queried": ["LOCAL_CURATED", "crossref", "openalex"],
           "errors": errors}
    if not live_ok and local:
        out["offline_mode"] = True
        out["note"] = ("外部 provider 当前失败（见 errors）; 以下结果来自已验证的"
                       "本地学术 registry（LOCAL_CURATED, 历史发现+策展）, 非实时检索")
    cache["searches"][key] = out
    for r in merged:
        cache["records"][r["source_record_id"]] = r
    _save_cache()
    return out


def get_record(source_record_id):
    rec = _load_cache()["records"].get(source_record_id)
    if rec is not None:
        return rec
    try:
        import scholarly_registry as SR
        return SR.record(source_record_id)
    except Exception:
        return None


# ── 模型可见精简视图（§26/§27）───────────────────────────────────
def model_view(rec):
    return {"source_record_id": rec["source_record_id"],
            "title": rec["title"],
            "authors": [a.get("name") for a in (rec.get("authors") or [])][:6],
            "year": rec["publication_year"],
            "publication_type": rec["publication_type"],
            "venue": rec["container_title"],
            "doi": rec["identifiers"].get("doi"),
            "source_category": rec.get("philosophical_role") or "UNKNOWN",
            "access_level": rec["access"]["level"],
            "provider": "/".join(rec["provenance"]["providers"]),
            "source_providers": rec["provenance"]["providers"],
            "retrieval_origin": rec.get("retrieval_origin", "LIVE"),
            "bibliographic_verified_fields": sorted(rec.get("provenance", {}).get("field_sources", {})),
            "note": "access_level 只反映已实际取得的证据; 不得凭标题推断论文内容"}
