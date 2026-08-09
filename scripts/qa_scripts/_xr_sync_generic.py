# -*- coding: utf-8 -*-
"""通用四层同步 + 五步验证：PA book_chapters/book_detail → DP backend/book_chapters + app/public
用法: python _xr_sync_generic.py <bid> [bid...]
五步验证: detail双端md5 / books.cc==detail.cc / meta三处md5 / toc.index==文件编号 / detail.toc==meta.toc
"""
import json, os, re, shutil, sys, hashlib
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PA_BC = 'f:/program/Python/PhiAgent/backend/data/book_chapters'
PA_BD = 'f:/program/Python/PhiAgent/backend/data/book_detail'
PA_BCAT = 'f:/program/Python/PhiAgent/backend/data/books_catalog.json'
DP_BC = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters'
DP_BD = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail'
DP_BCAT = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json'

def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()[:10]

def sync_chapter_dir(bid):
    src, dst = os.path.join(PA_BC, bid), os.path.join(DP_BC, bid)
    os.makedirs(dst, exist_ok=True)
    for f in os.listdir(src):
        if f.endswith('.json'):
            shutil.copy2(os.path.join(src, f), os.path.join(dst, f))

def sync_detail(bid):
    shutil.copy2(os.path.join(PA_BD, bid + '.json'), os.path.join(DP_BD, bid + '.json'))

for bid in sys.argv[1:]:
    print('=' * 60)
    print('同步 %s' % bid)
    sync_chapter_dir(bid)
    sync_detail(bid)
    print('  四层: PA bc/PA bd → DP bc/DP bd ✓')
    # 五步验证
    pa_bc = os.path.join(PA_BC, bid, 'meta.json')
    dp_bc = os.path.join(DP_BC, bid, 'meta.json')
    pa_bd = os.path.join(PA_BD, bid + '.json')
    dp_bd = os.path.join(DP_BD, bid + '.json')
    v1a, v1b = md5(pa_bd), md5(dp_bd)
    print('  [1] detail PA/DP md5: %s %s %s' % (v1a, v1b, '✓' if v1a == v1b else '✗!'))
    meta = json.load(open(pa_bc, encoding='utf-8'))
    detail = json.load(open(pa_bd, encoding='utf-8'))
    cc_meta = meta['chapterCount']
    cc_detail = detail.get('chapterCount')
    print('  [2] meta.cc=%d detail.cc=%s %s' % (cc_meta, cc_detail, '✓' if cc_meta == cc_detail else '✗!'))
    v3a, v3b, v3c = md5(pa_bc), md5(dp_bc), md5(os.path.join(DP_BC, bid, 'meta.json'))
    print('  [3] meta PA/DP/DP2 md5: %s %s %s %s' % (v3a, v3b, v3c, '✓' if v3a == v3b == v3c else '✗!'))
    # [4] toc index == 文件编号
    bad = []
    files = [f for f in os.listdir(os.path.join(PA_BC, bid)) if f.endswith('.json') and f != 'meta.json']
    for t in meta['toc']:
        if t['type'] == 'chapter':
            fn = str(t['index']) + '.json'
            if fn not in files:
                bad.append(fn)
    print('  [4] toc index 文件齐全 %s' % ('✓' if not bad else '✗ ' + str(bad)))
    # [5] detail.toc == meta.toc 对象格式
    dt, mt = detail.get('toc'), meta.get('toc')
    same = dt is not None and json.dumps(dt, ensure_ascii=False) == json.dumps(mt, ensure_ascii=False)
    print('  [5] detail.toc == meta.toc %s' % ('✓' if same else '✗!'))
    if not (v1a == v1b and cc_meta == cc_detail and v3a == v3b == v3c and not bad and same):
        print('  ⚠ 验证未全过，终止后续')
        sys.exit(1)
print('\n全部同步+验证通过 ✓')
