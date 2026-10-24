# -*- coding: utf-8 -*-
"""dp_intake_finalize.py — 178本正式入库收尾同步（单本/多本通用）

用法: python dp_intake_finalize.py <bid> [bid2 ...]

对每本书做（backend/data/book_chapters/{bid}/ 已重建完成后）：
  1. book_detail/{bid}.json ← meta 同步 chapterCount/chapterTitles/toc，加 intakeCompleted=true
  2. app/public/books.json + app/src/assets/books.json 条目同步 chapterCount + intakeCompleted
  3. app/public/philosopher/catalog.json 条目同步 chapterCount + intakeCompleted
  4. 章节文件镜像到 app/public/backend/data/book_chapters/{bid}/（MD5 一致）
  5. 自检：dict块/编号连续/meta-detail-books 一致

不发布、不提交 git；发布由 dp_book_round_coordination 锁流程另行处理。
"""
import hashlib
import json
import os
import shutil
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(BASE, 'backend', 'data', 'book_chapters')
MIRROR = os.path.join(BASE, 'app', 'public', 'backend', 'data', 'book_chapters')
DETAIL = os.path.join(BASE, 'app', 'public', 'book_detail')
BOOKS_FILES = [
    os.path.join(BASE, 'app', 'public', 'books.json'),
    os.path.join(BASE, 'app', 'src', 'assets', 'books.json'),
]
CATALOG = os.path.join(BASE, 'app', 'public', 'philosopher', 'catalog.json')


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def dump_json(path, obj):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def finalize(bid):
    fails = []
    src_dir = os.path.join(SRC, bid)
    meta = load_json(os.path.join(src_dir, 'meta.json'))
    n = meta['chapterCount']

    # 0. 自检章节文件
    for i in range(n):
        ch = load_json(os.path.join(src_dir, f'{i}.json'))
        if ch.get('index') != i:
            fails.append(f'{bid}:{i}.json index={ch.get("index")}')
        if ch.get('title') != meta['chapterTitles'][i]:
            fails.append(f'{bid}:{i}.json title != chapterTitles[{i}]')
        for bi, b in enumerate(ch.get('content', [])):
            if not isinstance(b, dict) or b.get('type') not in ('text', 'image', 'html'):
                fails.append(f'{bid}:{i}.json block{bi} bad type')
                break

    # 1. detail
    dpath = os.path.join(DETAIL, f'{bid}.json')
    detail = load_json(dpath)
    detail['chapterCount'] = n
    detail['chapterTitles'] = meta['chapterTitles']
    detail['toc'] = meta['toc']
    detail['intakeCompleted'] = True
    dump_json(dpath, detail)

    # 2. books.json ×2
    for bf in BOOKS_FILES:
        books = load_json(bf)
        hit = False
        for b in books:
            if b.get('id') == bid:
                b['chapterCount'] = n
                b['intakeCompleted'] = True
                hit = True
                break
        if not hit:
            fails.append(f'{bid}: books.json({os.path.basename(os.path.dirname(bf))}) 无条目')
        dump_json(bf, books)

    # 3. philosopher/catalog.json
    cat = load_json(CATALOG)
    hit = False
    for b in cat.get('books', []):
        if b.get('id') == bid:
            b['chapterCount'] = n
            b['intakeCompleted'] = True
            hit = True
            break
    if not hit:
        fails.append(f'{bid}: philosopher/catalog.json 无条目')
    dump_json(CATALOG, cat)

    # 4. 镜像
    mdir = os.path.join(MIRROR, bid)
    os.makedirs(mdir, exist_ok=True)
    for fn in os.listdir(src_dir):
        if fn.endswith('.json'):
            shutil.copy2(os.path.join(src_dir, fn), os.path.join(mdir, fn))
    # 清多余旧章节文件（0..n-1 之外的数字.json）
    for fn in os.listdir(mdir):
        if fn.endswith('.json') and fn != 'meta.json':
            stem = fn[:-5]
            if stem.isdigit() and int(stem) >= n:
                os.remove(os.path.join(mdir, fn))
    for i in range(n):
        a, b = os.path.join(src_dir, f'{i}.json'), os.path.join(mdir, f'{i}.json')
        if not os.path.exists(b) or md5(a) != md5(b):
            fails.append(f'{bid}: mirror {i}.json 不一致')

    return fails, n


def main():
    bids = [a for a in sys.argv[1:] if not a.startswith('-')]
    if not bids:
        print(__doc__)
        sys.exit(1)
    all_bad = []
    for bid in bids:
        fails, n = finalize(bid)
        status = 'OK' if not fails else 'FAIL'
        print(f'[{status}] {bid}: {n} 章')
        for f in fails:
            print('   -', f)
        all_bad += fails
    sys.exit(1 if all_bad else 0)


if __name__ == '__main__':
    main()
