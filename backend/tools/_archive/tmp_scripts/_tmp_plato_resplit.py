# -*- coding: utf-8 -*-
"""柏拉图对话集重切: 5章(乱) → 17章(前言+12篇对话+4附录), 双端同步
边界(3/4.json 合并全局块): 0/1=目录页(剔除)
1欧悌甫戎2-25 2申辩26-56 3格黎东57-73 4卡尔弥德74-108 5拉刻109-139
6吕锡140-155 7枚农156-208 8裴洞209-291 9会饮292-357 10治国358-499
11巴门尼德500-584 12智者585-610 13传611-655 14亚里士多德论656-691
15是"的学说692-705 16王太庆论706-803"""
import json, os, shutil

B = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy'
CD = B + r'\backend\data\book_chapters\35279e2e439d'
PD = B + r'\app\public\backend\data\book_chapters\35279e2e439d'

# 边界(左闭右开): 章索引 -> 全局块区间; 章0 用原0.json
BOUNDS = {
    1: (2, 26), 2: (26, 57), 3: (57, 74), 4: (74, 109), 5: (109, 140),
    6: (140, 156), 7: (156, 209), 8: (209, 292), 9: (292, 358), 10: (358, 500),
    11: (500, 585), 12: (585, 611), 13: (611, 656), 14: (656, 692),
    15: (692, 706), 16: (706, 804),
}
TITLES = {
    0: '前言', 1: '欧悌甫戎篇', 2: '苏格拉底的申辩篇', 3: '格黎东篇', 4: '卡尔弥德篇',
    5: '拉刻篇', 6: '吕锡篇', 7: '枚农篇', 8: '裴洞篇', 9: '会饮篇',
    10: '治国篇', 11: '巴门尼德篇', 12: '智者篇', 13: '苏格拉底、柏拉图传',
    14: '亚里士多德论柏拉图', 15: '柏拉图关于“是”的学说', 16: '王太庆论柏拉图哲学和翻译问题',
}

# 合并 3/4 为全局块流
blocks = []
for fi in (3, 4):
    ch = json.load(open(os.path.join(CD, '%d.json' % fi), encoding='utf-8'))
    for b in ch.get('content', []):
        blocks.append({'type': b.get('type', 'text'), 'value': b.get('value', '')})
print('全局块流:', len(blocks), '(应804)')

# 章0 保留原 0.json
old0 = json.load(open(os.path.join(CD, '0.json'), encoding='utf-8'))
chapters = [{'title': '前言', 'content': old0.get('content', [])}]

# 切章
for ci in range(1, 17):
    lo, hi = BOUNDS[ci]
    content = [b for b in blocks[lo:hi] if b.get('value', '').strip()]
    chapters.append({'title': TITLES[ci], 'content': content})
    print('章%d %s: 块 %d-%d, %d 块, %d 字符' % (ci, TITLES[ci], lo, hi - 1, len(content),
          sum(len(b['value']) for b in content)))

# 章首验证
print()
for ci in (1, 2, 3, 10, 12, 13, 14, 15, 16):
    c = chapters[ci]['content'][0]['value'][:45].replace('\n', '⏎')
    print('章%d 首: %s' % (ci, c))

# meta
old_meta = json.load(open(os.path.join(CD, 'meta.json'), encoding='utf-8'))
titles = [TITLES[i] for i in range(17)]
meta = {
    'bookId': old_meta['bookId'], 'title': old_meta['title'], 'author': old_meta['author'],
    'cover': old_meta.get('cover', ''), 'chapterCount': 17,
    'chapterTitles': titles,
    'toc': [{'type': 'section', 'title': t, 'index': i} for i, t in enumerate(titles)],
}

# 双端写
for d in (CD, PD):
    os.makedirs(d, exist_ok=True)
    for i, ch in enumerate(chapters):
        json.dump(ch, open(os.path.join(d, '%d.json' % i), 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(meta, open(os.path.join(d, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
# 删旧残留(5-16 旧编号在 public 可能不存在, 确保目录干净)
print()
print('backend 目录:', sorted(os.listdir(CD)))
print('public 目录:', sorted(os.listdir(PD)))

# book_detail 同步
dp = B + r'\backend\data\book_detail\35279e2e439d.json'
d = json.load(open(dp, encoding='utf-8'))
d['chapterCount'] = 17
d['chapterTitles'] = titles
d['toc'] = meta['toc']
json.dump(d, open(dp, 'w', encoding='utf-8'), ensure_ascii=False)
print('book_detail 同步: chapterCount=%d toc=%d 项' % (d['chapterCount'], len(d['toc'])))

# books_catalog 同步
cp = B + r'\backend\data\books_catalog.json'
cat = json.load(open(cp, encoding='utf-8'))
for item in cat['books']:
    if item['id'] == '35279e2e439d':
        item['chapterCount'] = 17
json.dump(cat, open(cp, 'w', encoding='utf-8'), ensure_ascii=False)
print('books_catalog 同步: 柏拉图对话集 chapterCount=17')

# 最终校验
print()
print('=== 校验 ===')
n = len(chapters)
total_chars = 0
for i in range(n):
    p = os.path.join(CD, '%d.json' % i)
    ch = json.load(open(p, encoding='utf-8'))
    total = sum(len(b.get('value', '')) for b in ch.get('content', []))
    total_chars += total
print('章节文件数: %d (0-%d.json 全存在)' % (n, n - 1))
print('全书总字符:', total_chars)
print('前端章节抽查 10.json:', json.load(open(os.path.join(CD, '10.json'), encoding='utf-8'))['title'])
