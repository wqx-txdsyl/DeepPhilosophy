"""Build a small school/author/book navigation index from the canonical public data."""
import argparse
import json
import os
from pathlib import Path

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_catalog(public):
    atlas = json.loads((public / 'gene/atlas.json').read_text(encoding='utf-8'))
    books = json.loads((public / 'books.json').read_text(encoding='utf-8'))
    philosophers = json.loads((public / 'philosophers.json').read_text(encoding='utf-8'))
    schools, branches = [], {}
    for item in atlas:
        detail = json.loads((public / 'schools/data' / item['detailFile']).read_text(encoding='utf-8'))
        schools.append({key: item[key] for key in ('name', 'detailFile', 'image', 'century')})
        for sub in detail.get('subSchools', []):
            if isinstance(sub, dict) and sub.get('name'):
                branches.setdefault(sub['name'], []).append(item['name'])
    people = []
    for name in philosophers:
        portrait = philosophers[name].get('portrait')
        if 'portrait' not in philosophers[name]:
            for ext in ('webp', 'jpg', 'png', 'jpeg'):
                file = public / 'philosopher' / f'{name}.{ext}'
                if file.is_file():
                    portrait = '/philosopher/' + file.name
                    break
        people.append({'name': name, 'portrait': portrait, 'era': philosophers[name].get('era', '')})
    aliases = json.loads((public / 'philosopher/catalog.json').read_text(encoding='utf-8')).get('aliases', {})
    return {'schools': schools, 'branches': branches, 'philosophers': people, 'aliases': aliases,
            'books': [{k: book.get(k) for k in ('id', 'title', 'author', 'cover', 'chapterCount', 'file_type')} for book in books]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    public = Path(BASE) / 'app/public'
    target = public / 'schools/catalog.json'
    data = build_catalog(public)
    content = json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n'
    if args.check:
        if not target.exists() or target.read_text(encoding='utf-8') != content:
            raise SystemExit('流派导航索引需要更新：python scripts/sync_school_catalog.py')
    else:
        target.write_text(content, encoding='utf-8')
    print(f"流派 {len(data['schools'])} · 子流派名称 {len(data['branches'])} · 作者 {len(data['philosophers'])} · 书籍 {len(data['books'])}")


if __name__ == '__main__':
    main()
