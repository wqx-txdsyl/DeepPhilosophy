"""Bounded public fetches for research providers. Credentials stay on fixed API hosts."""
import json
import http.client
import re
import urllib.error
import urllib.parse
import urllib.request
import zlib

import deep_web as web


class ResearchHTTPError(Exception):
    def __init__(self, code, status=None, retry_after=None, final_url=None):
        super().__init__(code)
        self.code=code;self.status=status;self.retry_after=retry_after;self.final_url=redact_url(final_url) if final_url else None


def redact_url(url):
    try:
        u=urllib.parse.urlsplit(url)
        query=urllib.parse.parse_qsl(u.query,keep_blank_values=True)
        hidden={'api_key','apikey','key','token','access_token','authorization'}
        query=[(k,'REDACTED' if k.lower() in hidden else v) for k,v in query]
        return urllib.parse.urlunsplit((u.scheme,u.netloc,u.path,urllib.parse.urlencode(query),''))
    except ValueError:return 'INVALID_URL'


class _NoCredentialRedirect(web._Redirects):
    def redirect_request(self, request, fp, code, message, headers, target):
        raise ResearchHTTPError('AUTHENTICATED_REDIRECT_REFUSED',code)


def fetch_bytes(url, *, accept='application/json', headers=None, data=None, max_bytes=15*1024*1024):
    try:
        canonical,host,_=web.public_url(url)
        extra=headers or {}
        authorized=any(k.lower() in {'authorization','x-api-key'} for k in extra)
        if authorized and (host not in {'api.openalex.org','api.semanticscholar.org','metaso.cn','api.deepseek.com'} or not canonical.startswith('https://')):
            raise ResearchHTTPError('CREDENTIAL_DESTINATION_REFUSED')
        if any(k.lower() in {'cookie','host','proxy-authorization'} for k in extra):
            raise ResearchHTTPError('UNSUPPORTED_RESEARCH_HEADER')
        h={'User-Agent':'DeepPhilosophy/1.0 (research source verification)','Accept':accept,'Accept-Encoding':'identity',**extra}
        request=urllib.request.Request(canonical,headers=h,data=data)
        observations=[]
        with web._ReadBudget() as budget:
            redirects=_NoCredentialRedirect() if authorized or any(k.lower() in {'api_key','apikey','access_token'} for k,_ in urllib.parse.parse_qsl(urllib.parse.urlsplit(canonical).query)) else web._Redirects()
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),redirects,web._PinnedHandler(observations,budget),web._PinnedTLSHandler(observations,budget))
            with opener.open(request,timeout=web.SOCKET_TIMEOUT) as response:
                raw=bytearray()
                while True:
                    budget.remaining();chunk=response.read1(min(65536,max_bytes+1-len(raw)));raw.extend(chunk)
                    if len(raw)>max_bytes:raise ResearchHTTPError('RESPONSE_TOO_LARGE')
                    if not chunk:break
                expected=response.headers.get('Content-Length')
                if expected and expected.isdecimal() and len(raw)!=int(expected):raise ResearchHTTPError('INCOMPLETE_RESPONSE')
                encoding=(response.headers.get('Content-Encoding') or 'identity').lower().strip()
                if encoding in {'gzip','deflate'}:
                    decoder=zlib.decompressobj(16+zlib.MAX_WBITS if encoding=='gzip' else zlib.MAX_WBITS)
                    raw=decoder.decompress(raw,max_bytes+1)
                    if len(raw)>max_bytes or decoder.unconsumed_tail:raise ResearchHTTPError('RESPONSE_TOO_LARGE')
                    if not decoder.eof or decoder.unused_data:raise ResearchHTTPError('INCOMPLETE_RESPONSE')
                elif encoding!='identity':raise ResearchHTTPError('UNSUPPORTED_ENCODING')
                return {'body':bytes(raw),'status':response.status,'url':response.geturl(),'content_type':response.headers.get_content_type(),'charset':response.headers.get_content_charset(),'network_modes':observations,'redirect_count':redirects.count}
    except ResearchHTTPError:raise
    except web.WebReadError as exc:raise ResearchHTTPError(str(exc)) from None
    except urllib.error.HTTPError as exc:
        code='AUTHENTICATION_REQUIRED' if exc.code==401 else 'ACCESS_DENIED' if exc.code==403 else 'RATE_LIMITED' if exc.code==429 else 'HTTP_UNAVAILABLE'
        raise ResearchHTTPError(code,exc.code,exc.headers.get('Retry-After'),exc.geturl()) from None
    except http.client.IncompleteRead:raise ResearchHTTPError('INCOMPLETE_RESPONSE') from None
    except (OSError,urllib.error.URLError,ValueError,http.client.HTTPException):raise ResearchHTTPError('NETWORK_UNAVAILABLE') from None


def fetch_json(url, **kwargs):
    response=fetch_bytes(url,**kwargs)
    try:
        value=json.loads(response['body'])
        if not isinstance(value,dict):raise ResearchHTTPError('INVALID_JSON_STRUCTURE')
        return value
    except (ValueError,UnicodeError):raise ResearchHTTPError('INVALID_JSON') from None
