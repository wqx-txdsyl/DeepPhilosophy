"""Public search with explicit provider receipts; no model or answer rewriting."""
import base64
import json
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from research_transport import fetch_bytes, ResearchHTTPError
from deepseek_web_search import search as native_search

USER_AGENT = 'Mozilla/5.0 (compatible; DeepPhilosophy/1.0)'


def query_candidates(query, results):
    """Reject plainly unrelated SERPs, not judge the truth of a source."""
    stop = {'the','of','a','an','and','in','on','to','for','with','is','what'}
    terms = list(dict.fromkeys(t.casefold() for t in re.findall(r'\w+', query)
                              if len(t) > 1 and t.casefold() not in stop))
    if not terms:
        return results
    kept = []
    for result in results:
        text = (result['title'] + ' ' + result.get('snippet','')).casefold()
        matched = sum(bool(re.search(r'(?<!\w)' + re.escape(t) + r's?(?!\w)', text))
                      if t.isascii() else t in text for t in terms)
        if matched >= min(2, len(terms)):
            kept.append(result)
    return kept


def result_url(value):
    value = str(value or '').strip()
    parsed = urllib.parse.urlsplit(value)
    if parsed.hostname in {'www.bing.com', 'cn.bing.com', 'bing.com'} and parsed.path == '/ck/a':
        encoded = urllib.parse.parse_qs(parsed.query).get('u', [''])[0]
        if not encoded.startswith('a1'):
            return None
        try:
            value = base64.urlsafe_b64decode(encoded[2:] + '=' * (-len(encoded[2:]) % 4)).decode('utf-8')
        except (ValueError, UnicodeError):
            return None
        parsed = urllib.parse.urlsplit(value)
    return value if parsed.scheme in {'https', 'http'} and parsed.hostname and not parsed.username else None


def parse_bing(text, rss=False):
    out = []
    if rss:
        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            raise ValueError('UNRECOGNIZED_SEARCH_RESPONSE') from None
        if root.tag != 'rss':
            raise ValueError('UNRECOGNIZED_SEARCH_RESPONSE')
        candidates = [(i.findtext('title'), i.findtext('link'), i.findtext('description')) for i in root.findall('./channel/item')]
    else:
        soup = BeautifulSoup(text, 'html.parser')
        candidates = []
        for item in soup.select('li.b_algo'):
            link = item.select_one('h2 a[href]')
            if link:
                paragraph = item.select_one('p')
                candidates.append((link.get_text(' ', strip=True), link.get('href'), paragraph.get_text(' ', strip=True) if paragraph else ''))
        # A home page, challenge or redesigned page is not evidence of zero matches.
        if not candidates:
            raise ValueError('NO_SEARCH_RESULT_BLOCKS')
    for title, url, snippet in candidates:
        url = result_url(url)
        if url and title and url not in {item['url'] for item in out}:
            out.append({'title': BeautifulSoup(title, 'html.parser').get_text(' ', strip=True),
                        'url': url, 'snippet': BeautifulSoup(snippet or '', 'html.parser').get_text(' ', strip=True)[:700]})
    if candidates and not out:
        raise ValueError('NO_USABLE_RESULT_LINKS')
    return out[:8]


def search(query):
    encoded = urllib.parse.quote(query)
    attempts, errors = [], []
    try:
        native = native_search(query)
        if native is not None:
            return native
    except ResearchHTTPError as exc:
        error = {'provider':'deepseek','error':exc.code,'http_status':exc.status,'retry_after':exc.retry_after}
        errors.append(error)
        attempts.append({**error,'status':'error'})
    market = 'zh-CN' if re.search(r'[\u3400-\u9fff]', query) else 'en-US'
    endpoints = [('bing', f'https://www.bing.com/search?q={encoded}&mkt={market}'),
                 ('bing_rss', f'https://www.bing.com/search?q={encoded}&format=rss&mkt={market}'),
                 ('en.wikipedia.org', f'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded}&format=json&srlimit=5'),
                 ('zh.wikipedia.org', f'https://zh.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded}&format=json&srlimit=5')]
    for provider, url in endpoints:
        try:
            response = fetch_bytes(url, accept='text/html,application/json,application/rss+xml',
                                   headers={'User-Agent': USER_AGENT}, max_bytes=2*1024*1024)
            text = response['body'].decode(response.get('charset') or 'utf-8', 'replace')
            if provider.startswith('bing'):
                raw = parse_bing(text, rss=provider == 'bing_rss')
                results = query_candidates(query, raw)
                if raw and not results:
                    raise ValueError('NO_QUERY_MATCH_IN_SEARCH_RESULTS')
            else:
                data = json.loads(text)
                if data.get('error') or not isinstance(data.get('query', {}).get('search'), list):
                    raise ValueError('UNRECOGNIZED_SEARCH_RESPONSE')
                results = [{'title': r['title'], 'url': f'https://{provider}/wiki/' + urllib.parse.quote(r['title'].replace(' ', '_')),
                            'snippet': BeautifulSoup(r.get('snippet', ''), 'html.parser').get_text(' ', strip=True)}
                           for r in data['query']['search'] if r.get('title')]
                if results:
                    results = query_candidates(query, results)
                    if not results:
                        raise ValueError('NO_QUERY_MATCH_IN_SEARCH_RESULTS')
            attempts.append({'provider': provider, 'http_status': response['status'],
                             'status': 'success' if results else 'empty', 'result_count': len(results)})
            if results:
                return {'query': query, 'results': results, 'source': provider,
                        'status': 'partial' if errors else 'success', 'provider_errors': errors,
                        'provider_attempts': attempts, 'fetched_at': time.time(),
                        'scope': 'encyclopedia_only' if 'wikipedia' in provider else 'web_search',
                        'note': '返回搜索摘要与链接，未读取目标网页正文。' + ('当前仅百科兜底，不是全面网页搜索。' if 'wikipedia' in provider else '')}
        except (ResearchHTTPError, ValueError, KeyError, TypeError, LookupError) as exc:
            error = {'provider': provider, 'error': exc.code if isinstance(exc, ResearchHTTPError) else str(exc)}
            if isinstance(exc, ResearchHTTPError):
                error.update(http_status=exc.status, retry_after=exc.retry_after)
            errors.append(error)
            attempts.append({**error, 'status': 'error'})
    status = 'error' if all(a['status'] == 'error' for a in attempts) else 'partial' if errors else 'empty'
    return {'query': query, 'results': [], 'status': status, 'provider_errors': errors,
            'provider_attempts': attempts, 'fetched_at': time.time(),
            'note': '检索未取得可用结果；请查看来源状态，不能据此推断相关内容不存在。'}
