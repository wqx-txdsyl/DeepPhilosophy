"""DeepSeek's native search via Messages; return source records, not model prose.

Protocol reference: deepseek-ai/deepseek-harness,
packages/web/web-search-deepseek/src/provider.ts.
The existing official DeepSeek credential is never forwarded to another host.
"""
import json
import time
from urllib.parse import urlsplit

from research_transport import fetch_json, ResearchHTTPError

ENDPOINT = 'https://api.deepseek.com/anthropic/v1/messages'


def parse_response(payload, query):
    blocks = payload.get('content') or []
    result_blocks = [b for b in blocks if b.get('type') == 'web_search_tool_result']
    if not result_blocks:
        raise ResearchHTTPError('NATIVE_SEARCH_NOT_EXECUTED')
    snippets = {}
    for block in blocks:
        if block.get('type') == 'text':
            for cite in block.get('citations') or []:
                if cite.get('url') and cite.get('cited_text'):
                    snippets.setdefault(cite['url'], cite['cited_text'])
    results, errors, seen = [], [], set()
    for block in result_blocks:
        content = block.get('content')
        if isinstance(content, dict):
            errors.append({'provider':'deepseek', 'error':content.get('error_code') or 'NATIVE_SEARCH_ERROR'})
            continue
        if not isinstance(content, list):
            raise ResearchHTTPError('MALFORMED_NATIVE_SEARCH_RESULTS')
        for item in content:
            if item.get('type') != 'web_search_result':
                continue
            url = item.get('url') or ''
            try:
                parsed = urlsplit(url)
            except ValueError:
                continue
            if parsed.scheme not in {'https','http'} or not parsed.hostname or parsed.username or url in seen:
                continue
            seen.add(url)
            results.append({'title':item.get('title') or url, 'url':url,
                            'snippet':snippets.get(url, ''), 'snippet_source':'provider_citation',
                            'page_age':item.get('page_age')})
    queries = [b.get('input', {}).get('query') for b in blocks if b.get('type') == 'server_tool_use' and b.get('name') == 'web_search']
    status = ('partial' if results else 'error') if errors else 'success' if results else 'empty'
    if status == 'error':
        raise ResearchHTTPError(errors[0]['error'])
    return {'query':query, 'results':results, 'source':'deepseek', 'status':status,
            'provider_errors':errors, 'provider_attempts':[{'provider':'deepseek','status':status,'queries':queries,'result_count':len(results)}],
            'fetched_at':time.time(), 'scope':'web_search', 'usage':payload.get('usage'),
            'note':'来源来自 DeepSeek 服务端实际搜索结果；摘录为供应商 citation，不等于本工具已核对网页全文。搜索摘要可能产生额外模型 token 费用。'}


def search(query):
    from routes.agent_llm import API_KEY, API_URL, MODEL
    configured = urlsplit(API_URL)
    if configured.hostname != 'api.deepseek.com' or configured.scheme != 'https' or not API_KEY:
        return None
    payload = fetch_json(ENDPOINT, headers={'x-api-key':API_KEY, 'anthropic-version':'2023-06-01',
                                          'Content-Type':'application/json'},
                         data=json.dumps({'model':MODEL, 'max_tokens':4096,
                                          'messages':[{'role':'user','content':f'Perform a web search for the query: {query}'}],
                                          'tools':[{'type':'web_search_20250305','name':'web_search','max_uses':5}]}).encode())
    return parse_response(payload, query)
