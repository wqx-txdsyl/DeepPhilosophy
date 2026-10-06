"""Preview philosophers: soul.md is the sole persona source; texts are evidence.

This registry and runtime are independent of the existing Nietzsche bundle.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'philosopher_agents'


@lru_cache(maxsize=1)
def catalog():
    rows = json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8'))['agents']
    result = {}
    for row in rows:
        key = row['key']
        if not re.fullmatch(r'[a-z][a-z0-9_]*', key) or key in {'general', 'nietzsche'} or key in result:
            raise ValueError(f'Invalid preview agent: {key}')
        if not (ROOT / key / 'soul.md').is_file():
            raise ValueError(f'Missing soul.md: {key}')
        result[key] = row
    if len(result) != 119:
        raise ValueError('The preview roster must contain exactly 119 philosophers')
    return result


def is_soul_agent(key):
    return key in catalog()


def soul_prompt(key, language='zh'):
    text = (ROOT / key / 'soul.md').read_text(encoding='utf-8')
    return text + ('\n\n本轮使用英文回答。原典可以保留原语言。' if language == 'en'
                   else '\n\n本轮使用中文回答。原典可以保留原语言。')


def normalized(value):
    return re.sub(r'[\W_]+', '', str(value)).casefold()


def local_books(key):
    from routes.agent_core import get_books
    spec = catalog()[key]
    authors = [normalized(a) for a in spec['author_aliases']]
    works = [normalized(w) for w in spec['works']]
    result = []
    for book in get_books():
        author, title = normalized(book.get('author', '')), normalized(book.get('title', ''))
        # Names match whole names or a prefixed full name, not arbitrary substrings.
        by_author = any(author == a or author.endswith(a) for a in authors if len(a) >= 2)
        by_work = any(title == w or title.startswith(w + suffix)
                      for w in works for suffix in ('译注', '注疏', '集注', '全译', '校注'))
        if by_author or by_work:
            result.append(book)
    return result


def public_agents():
    from routes.agent_core import CHAPTERS_DIR
    out = []
    for key, spec in catalog().items():
        books = local_books(key)
        readable = [b for b in books if (CHAPTERS_DIR / b['id']).is_dir()
                    and any((CHAPTERS_DIR / b['id']).glob('[0-9]*.json'))]
        out.append({**{k: spec[k] for k in ('key', 'name', 'name_en', 'tradition', 'tagline', 'portrait')},
                    'subtitle': '测试版 · ' + spec['tagline'], 'status': 'preview',
                    'local_primary_book_count': len(readable),
                    'primary_access': 'local_and_online' if readable else 'online_discovery',
                    'works': spec['works']})
    return out
