# -*- coding: utf-8 -*-
"""16 本 OCR 书: 超长块(>2400字符)按中英句读拆分 + public 双写 + 康德句读 public 残留清理
参照读资本论先例: minlen=800, maxlen=2400"""
import json, os, hashlib, re, shutil

B = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
CD = B + '/backend/data/book_chapters'
PUB = B + '/app/public/backend/data/book_chapters'
ck = json.load(open(B + '/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))

CUT_PAT = re.compile(r'[。！？；…]["”』」）】\'）]*|[.!?]["\'）]*(?=\s|$)')

def split_block(text, minlen=800, maxlen=2400):
    """按句读贪心切分: 每段 [minlen, maxlen] 之间取最大切点; 无切点则硬切 maxlen"""
    if len(text) <= maxlen:
        return [text]
    cuts = [m.end() for m in CUT_PAT.finditer(text) if m.end() < len(text)]
    out, start = [], 0
    while len(text) - start > maxlen:
        hi = start + maxlen
        cands = [c for c in cuts if start + minlen <= c <= hi]
        if cands:
            c = cands[-1]
        else:
            cands2 = [c for c in cuts if c > hi]
            c = cands2[0] if cands2 else hi
        if c <= start:
            c = min(hi, len(text))
        out.append(text[start:c])
        start = c
    out.append(text[start:])
    return out

rels = [rel for rel, v in ck['books'].items() if v.get('src') == 'ocr']
total_blocks_split = 0
total_bad_blocks = 0
for rel in rels:
    bid = hashlib.md5(rel.encode()).hexdigest()[:12]
    cdir = os.path.join(CD, bid)
    pdir = os.path.join(PUB, bid)
    mp = os.path.join(cdir, 'meta.json')
    m = json.load(open(mp, encoding='utf-8'))
    n = m['chapterCount']
    n_split = 0
    n_bad = 0
    maxlen = 0
    for i in range(n):
        p = os.path.join(cdir, '%d.json' % i)
        ch = json.load(open(p, encoding='utf-8'))
        newblocks = []
        for b in ch.get('content', []):
            v = b.get('value', '')
            if b.get('type') == 'text' and len(v) > 2400:
                parts = split_block(v)
                newblocks.extend({'type': 'text', 'value': pt} for pt in parts)
                n_split += len(parts) - 1
                n_bad += 1
                maxlen = max(maxlen, max(len(pt) for pt in parts))
            else:
                newblocks.append(b)
        ch['content'] = newblocks
        json.dump(ch, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
        shutil.copy2(p, os.path.join(pdir, '%d.json' % i))
    total_blocks_split += n_split
    total_bad_blocks += n_bad
    if n_bad:
        print('%-50s 超长块=%d 拆成 %d 段 (最大新块 %d)' % (rel[:46], n_bad, n_split + n_bad, maxlen))
    else:
        print('%-50s 无超长块' % rel[:46])

print()
print('总超长块:', total_bad_blocks, '| 新增段:', total_blocks_split)

# 康德句读 public 残留清理: 只保留 meta.json + 0..n-1.json
rel2 = '西方/伊曼努尔·康德/康德《实践理性批判》句读.pdf'
bid2 = hashlib.md5(rel2.encode()).hexdigest()[:12]
pdir2 = os.path.join(PUB, bid2)
m2 = json.load(open(os.path.join(CD, bid2, 'meta.json'), encoding='utf-8'))
keep = set(['meta.json'] + ['%d.json' % i for i in range(m2['chapterCount'])])
removed = []
for f in os.listdir(pdir2):
    if f not in keep:
        os.remove(os.path.join(pdir2, f))
        removed.append(f)
print('康德句读 public 清理残留:', removed)
