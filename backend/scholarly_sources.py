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

CONNECT_TIMEOUT = 8
READ_TIMEOUT = 20
MAX_REDIRECTS = 4
MAX_BYTES = 5 * 1024 * 1024   # full text 不无界下载
USER_AGENT = "DeepPhilosophy-PhiAgent/0.7 (scholarly metadata; contact: site-admin)"

SCHEMA_VERSION = "o7c-1"
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
        # 198.18.0.0/15（RFC2544 benchmark）在本机被 VPN fake-IP DNS 用作映射段,
        # 实际流量经代理出网; 真实 SSRF 面（loopback/RFC1918/link-local/file）仍硬禁。
        if ip in ipaddress.ip_network("198.18.0.0/15"):
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return False, f"private/reserved ip {ip}"
    return True, "ok"


def _http_get(url, accept="application/json"):
    """带硬上限的 GET。返回 (status, bytes)；错误抛 ProviderError。"""
    ok, why = _url_guard(url)
    if not ok:
        raise ProviderError("URL_BLOCKED", why)
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT, "Accept": accept,
        "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=CONNECT_TIMEOUT) as r:
        data = r.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ProviderError("RESPONSE_TOO_LARGE", url)
        return r.status, data


class ProviderError(Exception):
    def __init__(self, kind, detail=""):
        super().__init__(f"{kind}: {detail}")
        self.kind = kind          # PROVIDER_TIMEOUT / PROVIDER_RATE_LIMIT /
        self.detail = detail      # PROVIDER_UNAVAILABLE / MALFORMED / URL_BLOCKED …


def _get_json(url):
    try:
        status, data = _http_get(url)
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
        return json.loads(data.decode("utf-8", "replace"))
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
    url = (f"https://api.openalex.org/works?search={q}&per-page={min(limit, 20)}"
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
    # OA full text location（§16: 合法可解析位置才 FULL_TEXT_AVAILABLE）
    oa_url = None
    for r in provider_records:
        if (r.get("oa_pdf_url") or "").startswith(("https://", "http://")):
            oa_url = r["oa_pdf_url"]
            break
    if oa_url and rec["access"]["level"] == "ABSTRACT_AVAILABLE":
        rec["access"] = {"level": "FULL_TEXT_AVAILABLE",
                         "evidence": f"OA pdf url from provider record: {oa_url}",
                         "checked_at": int(time.time()),
                         "full_text_url": oa_url, "content_hash": None}
    return rec


# ── Access state machine（§13-§18）───────────────────────────────
def get_evidence(rec, requested_access):
    """按请求取实际 evidence; 严格逐级, 只升不降。返回 (record, result_info)。"""
    before = rec["access"]["level"]
    info = {"source_record_id": rec["source_record_id"],
            "access_level_before": before, "access_level_after": before,
            "full_text_status": None, "evidence_passages": [],
            "passage_locators": [], "source_url": None, "content_hash": None,
            "access_notes": ""}
    if rec["abstract"]["text"]:
        info["abstract"] = dict(rec["abstract"])
    if requested_access == "ABSTRACT":
        if rec["abstract"]["text"]:
            info["access_level_after"] = "ABSTRACT_AVAILABLE"
            info["access_notes"] = "abstract returned; 来源与 hash 见 abstract 字段"
        else:
            info["access_notes"] = "abstract 未取得: 保持 METADATA_ONLY（不得凭 title 推断内容）"
        return rec, info

    # FULL_TEXT_IF_LEGALLY_AVAILABLE
    if rec["access"]["level"] in ("METADATA_ONLY", "ABSTRACT_AVAILABLE"):
        info["access_notes"] = ("无合法可访问 full-text location（provider record "
                                "未提供 OA 位置）; 不因 DOI landing page 存在而升级")
        return rec, info
    url = rec["access"].get("full_text_url")
    info["source_url"] = url
    try:
        status, data = _http_get(url, accept="application/pdf,text/html,*/*")
    except ProviderError as e:
        info["full_text_status"] = f"FETCH_FAILED:{e.kind}"
        info["access_notes"] = f"full text 获取失败（{e.kind}）; 保持 FULL_TEXT_AVAILABLE 不虚报已读"
        return rec, info
    text = _extract_text(data, url)
    if not text or len(text.strip()) < 200:
        info["full_text_status"] = "PARSE_FAILED"
        info["access_notes"] = "body 解析未取得有意义内容; 不升级 FULL_TEXT_READ"
        return rec, info
    chash = hashlib.sha256(data).hexdigest()
    rec["access"] = {"level": "FULL_TEXT_READ",
                     "evidence": "fetched+parsed body obtained",
                     "checked_at": int(time.time()),
                     "full_text_url": url, "content_hash": chash,
                     "content_length": len(text), "parser": "plain-text-heuristic"}
    info.update({"access_level_after": "FULL_TEXT_READ",
                 "full_text_status": "READ",
                 "content_hash": chash,
                 "evidence_passages": _top_passages(text, query_terms=None),
                 "access_notes": ("全文已内部解析; 返回相关节选段落而非整篇复制"
                                  "（§21 copyright-safe）")})
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


def search_scholarship(query, philosopher=None, work=None, year_from=None,
                       year_to=None, limit=8):
    """主入口: 双 provider 检索 → 归一 → canonical 去重。

    返回 {"results": [...], "providers_queried": [...], "errors": [...]},
    provider 失败以 errors 保留（≠ 没有文献）。"""
    q = " ".join(filter(None, [philosopher, work, query])).strip()
    key = json.dumps([q, year_from, year_to, limit], ensure_ascii=False)
    cache = _load_cache()
    if key in cache["searches"]:
        return cache["searches"][key]
    results, errors = [], []
    for name, fn in (("crossref", search_crossref), ("openalex", search_openalex)):
        try:
            results.extend(fn(q, limit=limit, year_from=year_from, year_to=year_to))
        except ProviderError as e:
            errors.append({"provider": name, "error": e.kind, "detail": e.detail})
    canon = merge_records(results)
    canon.sort(key=lambda r: -(r.get("provider_records", [{}])[0].get("cited_by") or 0))
    out = {"query": q, "results": canon[:limit],
           "providers_queried": ["crossref", "openalex"], "errors": errors}
    cache["searches"][key] = out
    for r in canon:
        cache["records"][r["source_record_id"]] = r
    _save_cache()
    return out


def get_record(source_record_id):
    return _load_cache()["records"].get(source_record_id)


# ── 模型可见精简视图（§26/§27）───────────────────────────────────
def model_view(rec):
    return {"source_record_id": rec["source_record_id"],
            "title": rec["title"],
            "authors": [a.get("name") for a in (rec.get("authors") or [])][:6],
            "year": rec["publication_year"],
            "publication_type": rec["publication_type"],
            "venue": rec["container_title"],
            "doi": rec["identifiers"].get("doi"),
            "source_category": ("SCHOLARLY_SECONDARY"
                                if rec["publication_type"] == "JOURNAL_ARTICLE" else "UNKNOWN"),
            "access_level": rec["access"]["level"],
            "provider": "/".join(rec["provenance"]["providers"]),
            "bibliographic_verified_fields": sorted(rec["provenance"]["field_sources"]),
            "note": "access_level 只反映已实际取得的证据; 不得凭标题推断论文内容"}
