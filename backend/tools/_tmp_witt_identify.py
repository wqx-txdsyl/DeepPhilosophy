# -*- coding: utf-8 -*-
"""维特根斯坦文集 (c0e78ea6f80a): 逐章内容鉴定 → 判断各章属于哪一卷"""
import json, os

B = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
D = B + '/backend/data/book_chapters/c0e78ea6f80a'

def get_text(fn):
    ch = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    return ''.join(b.get('value', '') for b in ch.get('content', []))

# 各卷标志性内容（前 1000 字符内搜索更准）
MARKERS = {
    '第1卷 战时笔记': ['14.8.', '14.9.', '15.', '入伍', '克拉科夫', '1914'],
    '第2卷 逻辑哲学论': ['世界是一切', '1 世界', '图像', '摹状', '显示'],
    '第3卷 哲学语法': ['语法', '语言游戏', '句法规则'],
    '第4卷 哲学研究': ['奥古斯丁', '语言游戏', '私人语言'],
    '第5卷 数学基础研究': ['数学证明', '递归', '游戏', '基数', '归纳'],
    '第6卷 心理学最后著作': ['LS I', 'LS II', '内心', '心理'],
    '第7卷 论颜色': ['颜色', '色调', '褐色'],
    '第8卷 论确定性': ['一只手', '确信', '怀疑', '错误'],
}

files = sorted([f for f in os.listdir(D) if f.endswith('.json') and f != 'meta.json'], key=lambda x: int(x.split('.')[0]))
for fn in files:
    ch = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    t = get_text(fn)
    head = t[:100].replace('\n', ' ')
    head1000 = t[:1000]
    scores = []
    for vol, kws in MARKERS.items():
        s = sum(head1000.count(k) for k in kws)
        scores.append((s, vol))
    scores.sort(reverse=True)
    top = ' | '.join('%s(%d)' % (v, s) for s, v in scores[:3])
    print('%s %-24s' % (fn, (ch.get('title') or '?')[:20]))
    print('   开头: %s' % head[:80])
    print('   判定: %s' % top)
