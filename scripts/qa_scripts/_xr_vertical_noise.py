# -*- coding: utf-8 -*-
"""快乐的科学(48f7bf321598) 竖排 OCR 噪声清洗：
竖排标题被 OCR 成 汉字-拉丁字母交替段（如"一快p乐的pK科p学SZp1."）
→ 删除噪声段 + 清理开头残留（汉字-字母-汉字残余 + 竖排页码"1."），保留横排正文
⚠ 正则必须字母 only：汉字-数字交替（"自1885年4月"/"1882年1月29日"/"第352页14行"）
  是日期页码，绝不能命中（2026-08-09 曾误删已 git 恢复）
"""
import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

D = 'f:/program/Python/PhiAgent/backend/data/book_chapters/48f7bf321598'
# 汉字-字母交替段（≥2 次交替，避免脚注"的1在"单次命中）
NOISE = re.compile(r'[一-鿿](?:[A-Za-z]+[一-鿿]){2,}[A-Za-z]*')
# 竖排标题残余：汉字-字母-汉字（"一快p乐"只剩 1 次交替，NOISE ≥2 次不命中）
HEAD_MIX = re.compile(r'^[一-鿿]+[A-Za-z]+[一-鿿]')
# 竖排页码"1."：只清块开头（正文中间的日期数字不受影响）
HEAD_PAGE = re.compile(r'^[0-9]+[.。、，]*')

total = 0
for f in sorted(os.listdir(D), key=lambda x: int(x[:-5]) if x.endswith('.json') and x != 'meta.json' else -1):
    if not f.endswith('.json') or f == 'meta.json':
        continue
    p = os.path.join(D, f)
    ch = json.load(open(p, encoding='utf-8'))
    changed = False
    for b in ch.get('content', []):
        if b.get('type') != 'text':
            continue
        v = b['value']
        if not re.search(r'[A-Za-z]', v):
            continue  # 无字母不可能有竖排噪声
        nv = NOISE.sub('', v)
        nv = HEAD_MIX.sub('', nv)
        nv = nv.lstrip(' 　')
        nv = HEAD_PAGE.sub('', nv)
        if nv != v:
            print('[%s] %s\n   → %s' % (f, v[:46], nv[:46]))
            b['value'] = nv
            changed = True
            total += 1
    if changed:
        json.dump(ch, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
print('清洗 %d 块' % total)
