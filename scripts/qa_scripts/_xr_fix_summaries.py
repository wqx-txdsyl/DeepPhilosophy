# -*- coding: utf-8 -*-
"""book_summaries.json 补齐：catalog 403 本 summary 全量同步进 summaries 缓存
（DP Render 后端 OSS 索引书单走 generate_summary → 查 DP book_summaries.json → 无条目=模板
"《X》是Y的著作，PDF格式，约Z MB" 覆盖前端静态对简介 = 简介被吞 2026-08-09 哲学规劝录事故）
规则：title||author、title 双键 + OSS 段作者键（Render 的 key 是 OSS 路径段作者，单作者）补入；
      已有非模板条目不动；模板条目（含"格式"+"MB"）覆盖
"""
import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')

CAT = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/books_catalog.json'
SUM = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_summaries.json'
OSS = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/oss_manifest.json'

cat = json.load(open(CAT, encoding='utf-8'))['books']
sums = json.load(open(SUM, encoding='utf-8'))

TPL = re.compile(r'格式，约[\d.]+MB')

# title→summary 索引（catalog 为对简介权威源）
by_title = {}
for b in cat:
    by_title.setdefault(b.get('title', ''), []).append(b)

added = []      # 新补
fixed = []      # 模板覆盖
skipped = []    # 已有且非模板（保留）
for b in cat:
    title, author = b.get('title', ''), b.get('author', '')
    summ = b.get('summary', '')
    if not title or not summ:
        continue
    for key in (f'{title}||{author}', title):
        cur = sums.get(key)
        if cur and cur.get('summary'):
            if TPL.search(cur['summary']):
                sums[key] = {'summary': summ, 'tags': b.get('tags', [])}
                fixed.append((key, cur['summary'][:20]))
            else:
                skipped.append(key)
        else:
            sums[key] = {'summary': summ, 'tags': b.get('tags', [])}
            added.append(key)

# OSS 路径段作者键（Render scan_books 的 author=OSS 段，与 catalog 合并作者不一致）
oss_fixed = 0
try:
    mani = json.load(open(OSS, encoding='utf-8'))
    for rel_path in mani:
        parts = rel_path.split('/')
        if len(parts) < 3:
            continue
        seg_author = parts[1].replace('###合集&概述###', '合集&概述')
        title = parts[-1][:-4] if parts[-1].lower().endswith(('.pdf', '.epub', '.txt')) else parts[-1]
        key = f'{title}||{seg_author}'
        if key in sums:
            continue
        cands = by_title.get(title)
        if not cands:
            continue
        summ = cands[0].get('summary')
        if summ:
            sums[key] = {'summary': summ, 'tags': cands[0].get('tags', [])}
            oss_fixed += 1
except FileNotFoundError:
    pass

json.dump(sums, open(SUM, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('新增 %d 键, 模板覆盖 %d 键, 已有保留 %d 键, OSS段作者键 %d 个, 缓存总条数 %d'
      % (len(added), len(fixed), len(skipped), oss_fixed, len(sums)))
print('新增样例:', added[:5])
print('模板覆盖:', fixed[:5])

# 验证哲学规劝录（Render 的 key 是 OSS 段作者单名）
for key in ('哲学规劝录 哲学的慰藉||扬布里柯', '哲学规劝录 哲学的慰藉'):
    s = sums.get(key)
    print('验证 %r → %s' % (key, s['summary'][:40] if s else '无'))
