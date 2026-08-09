# -*- coding: utf-8 -*-
"""通用四步验证：单本书（双端 md5 / chapterCount / meta 三处 / toc 集合）
用法: python _xr_verify_generic.py <bid>
"""
import json, os, re, sys, hashlib

def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()[:8]

def verify(bid):
    DP = f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}'
    DP_PUB = f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{bid}'
    PA = f'f:/program/Python/PhiAgent/backend/data/book_chapters/{bid}'
    dp_detail = f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{bid}.json'
    pa_detail = f'f:/program/Python/PhiAgent/app/public/book_detail/{bid}.json'

    print(f'=== {bid} 四步验证 ===')
    ok = True

    # ① detail 双端 md5
    if os.path.exists(dp_detail) and os.path.exists(pa_detail):
        a, b = md5(dp_detail), md5(pa_detail)
        st = '✓' if a == b else '✗'
        if a != b: ok = False
        print(f'  ① detail 双端 md5: {a} / {b} {st}')
    else:
        print(f'  ① detail: DP={os.path.exists(dp_detail)} PA={os.path.exists(pa_detail)}')
        ok = False

    # ② chapterCount 一致性（双端 books.json vs detail）
    for name, p in (('DP', 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json'),
                    ('PA', 'f:/program/Python/PhiAgent/app/public/books.json')):
        if not os.path.exists(p):
            continue
        bk = json.load(open(p, encoding='utf-8'))
        b = next((x for x in bk if x.get('id') == bid), None)
        if not b:
            print(f'  ② {name} books.json 无此书')
            ok = False
            continue
        d = json.load(open(dp_detail if name == 'DP' else pa_detail, encoding='utf-8')) if os.path.exists(dp_detail if name == 'DP' else pa_detail) else {}
        dcc = d.get('chapterCount', d.get('chapters_count'))
        cc = b.get('chapterCount')
        st = '✓' if dcc == cc else f'✗ detail={dcc} books={cc}'
        if dcc != cc: ok = False
        print(f'  ② {name} books cc={cc} vs detail cc={dcc} {st}')

    # ③ meta 三处 md5（存在才比）
    metas = []
    for name, p in (('DP', DP), ('DP_PUB', DP_PUB), ('PA', PA)):
        m = os.path.join(p, 'meta.json')
        if os.path.exists(m):
            metas.append((name, md5(m)))
    if metas:
        same = all(m[1] == metas[0][1] for m in metas)
        st = '✓' if same else '✗'
        if not same: ok = False
        print(f'  ③ meta 三处: ' + ' / '.join(f'{n}={h}' for n, h in metas) + f' {st}')
    else:
        print('  ③ meta 不存在（可能无章节）')
        ok = False

    # ④ toc index 集合 == 章节文件编号
    if metas:
        meta_path = os.path.join(DP, 'meta.json') if os.path.exists(os.path.join(DP, 'meta.json')) else os.path.join(PA, 'meta.json')
        m = json.load(open(meta_path, encoding='utf-8'))
        ch_dir = os.path.dirname(meta_path)
        if os.path.isdir(ch_dir):
            files = {int(f[:-5]) for f in os.listdir(ch_dir) if f.endswith('.json') and f != 'meta.json'}
            tidx = {t.get('index') for t in m.get('toc', [])}
            st = '✓' if tidx == files else f'✗ toc({len(tidx)}) vs files({len(files)})'
            if tidx != files: ok = False
            print(f'  ④ toc index 集合 == 文件编号: {st}')
            if tidx != files:
                print(f'     toc-only: {sorted(tidx - files)}  file-only: {sorted(files - tidx)[:8]}')
            # index < chapterCount
            cc = None
            bk = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json', encoding='utf-8'))
            b = next((x for x in bk if x.get('id') == bid), None)
            cc = b.get('chapterCount') if b else None
            if cc is not None:
                over = [t for t in m.get('toc', []) if t.get('index') >= cc]
                st = '✓' if not over else f'✗ {len(over)} 个 index >= cc'
                if over: ok = False
                print(f'  index < chapterCount({cc}): {st}')

    print('=== 结果:', '全部通过 ✓' if ok else '存在问题 ✗', '===')
    return ok

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python _xr_verify_generic.py <bid>')
        sys.exit(1)
    sys.exit(0 if verify(sys.argv[1]) else 1)
