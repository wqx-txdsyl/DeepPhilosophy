# -*- coding: utf-8 -*-
"""柏拉图对话集: 清洗 Stephanus 页码标注残留的孤立大写字母
规则(仅正文对话章 01-12, 附录/论文章 00/13/15/16 跳过):
  1. 单独成行 ^[A-Z]{1,4}$ (L/V/H/B/C/D/E 等) → 删行
  2. 单独成行 ^St\.[IVX]+$ (St.III) → 删行
  3. 单独成行 ^\d{1,4}[A-Za-z]?$ (178.A / 57A 页码) → 删行
  4. 嵌句中单字母 A-E 且两侧紧邻中文/行边界 → 删字母(前后拼接)
--apply 双端写回; 默认 dry-run 打印样本
"""
import json, re, os, sys, shutil, hashlib

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
D = BASE + '/backend/data/book_chapters/35279e2e439d'
P = BASE + '/app/public/backend/data/book_chapters/35279e2e439d'
APPLY = '--apply' in sys.argv

ALONE = re.compile(r'^[A-Z]{1,4}$')
ST = re.compile(r'^St\.[IVX]{1,4}$')
PGNO = re.compile(r'^\d{1,4}[A-Za-z]?$')
INLINE = re.compile(r'(?<![A-Za-z0-9])[A-E](?![A-Za-z0-9])')
CJK = r'\u4e00-\u9fff'
# 嵌句中: 两侧非字母/数字/点(即中文、换行、行首行尾、标点) 的单字母 A-E
# 排除: 英文缩写(B.Jowett→B后有点)、正文符号(SP/S/P→两侧字母数字)、希腊字母表
INLINE_BOUND = re.compile(r'(?<![A-Za-z0-9.])[A-E](?![A-Za-z0-9.])')

def clean_text(t):
    lines = t.split('\n')
    out = []
    for ln in lines:
        s = ln.strip()
        if ALONE.match(s) or ST.match(s) or PGNO.match(s):
            continue
        # 嵌句中: 行内处理
        out.append(INLINE_BOUND.sub('', ln))
    return '\n'.join(out)

print('== 嵌句中删除样本 ==')
samples = []
for i in range(1, 13):
    ch = json.load(open(D + '/%d.json' % i, encoding='utf-8'))
    for b in ch['content']:
        if b.get('type') != 'text':
            continue
        v = b.get('value', '')
        m = INLINE_BOUND.search(v)
        if m and len(samples) < 10:
            s = max(0, m.start() - 14); e = min(len(v), m.end() + 14)
            samples.append('章%02d: …%s…' % (i, v[s:e].replace('\n', '|')))
        break
for s_ in samples:
    print(' ', s_)

print()
print('== 每章清洗量 (字符数: 删行 + 嵌句) ==')
total = 0
for i in range(1, 13):
    ch = json.load(open(D + '/%d.json' % i, encoding='utf-8'))
    before = after = 0
    for b in ch['content']:
        if b.get('type') != 'text':
            continue
        v = b.get('value', '')
        before += len(v)
        after += len(clean_text(v))
    n = before - after
    total += n
    print('章%02d: -%d 字' % (i, n))
print('合计: -%d 字符' % total)

if APPLY:
    for i in range(1, 13):
        fp = D + '/%d.json' % i
        ch = json.load(open(fp, encoding='utf-8'))
        for b in ch['content']:
            if b.get('type') == 'text':
                b['value'] = clean_text(b['value'])
        json.dump(ch, open(fp, 'w', encoding='utf-8'), ensure_ascii=False)
    # public 双写
    for i in range(1, 13):
        shutil.copyfile(D + '/%d.json' % i, P + '/%d.json' % i)
    # MD5 验证
    bad = 0
    for f in os.listdir(D):
        a = hashlib.md5(open(D + '/' + f, 'rb').read()).hexdigest()
        b = hashlib.md5(open(P + '/' + f, 'rb').read()).hexdigest()
        if a != b:
            bad += 1
    print('已写回双端 (章01-12), MD5 不一致: %d' % bad)
