"""Refresh the public genealogy index from the existing school detail JSON files."""
import argparse
import json
import os
from pathlib import Path

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check without writing the index')
    args = parser.parse_args()
    public = Path(BASE) / 'app' / 'public'
    index_path = public / 'gene' / 'atlas.json'
    catalog = json.loads(index_path.read_text(encoding='utf-8'))
    changed = []
    for school in catalog:
        detail = json.loads((public / 'schools' / 'data' / school['detailFile']).read_text(encoding='utf-8'))
        thinkers = [{'name': thinker['name'], 'key': thinker.get('key') or '', 'influence': float(thinker.get('influence') or 0)} for thinker in detail.get('thinkers', []) if thinker.get('name')]
        if school['thinkers'] != thinkers:
            changed.append(school['name'])
            school['thinkers'] = thinkers
    if args.check and changed:
        raise SystemExit('谱系索引需要更新：' + '、'.join(changed))
    if changed and not args.check:
        index_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'谱系索引：{len(catalog)} 个流派，{len(changed)} 个更新')


if __name__ == '__main__':
    main()
