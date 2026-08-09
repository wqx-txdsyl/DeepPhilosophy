# -*- coding: utf-8 -*-
"""打印柏拉图切分边界块内容, 精确定位每篇首块"""
import json, os, re

CD = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\book_chapters\35279e2e439d'

blocks = []
for fi in (3, 4):
    ch = json.load(open(os.path.join(CD, '%d.json' % fi), encoding='utf-8'))
    for b in ch.get('content', []):
        blocks.append((fi, b.get('value', '')))
print('总块数:', len(blocks))

def show(i, label):
    if 0 <= i < len(blocks):
        print('--- [%d] %s (来自%d.json) ---' % (i, label, blocks[i][0]))
        print('   ', blocks[i][1][:120].replace('\n', '⏎'))
        print()

# 已知锚点
ANCH = {2: '欧悌甫戎篇首', 57: '格黎东篇首', 74: '卡尔弥德篇首', 109: '拉刻篇首',
        140: '吕锡篇首', 156: '枚农篇首', 209: '裴洞篇首', 292: '会饮篇首',
        358: '治国篇首', 500: '巴门尼德篇首', 585: '智者篇首'}
for i, l in ANCH.items():
    show(i, l)

# 申辩篇首: 找 "Su.1" 或 "（伦理的）" 在 2-57 之间
for i in range(3, 57):
    if 'Su.1' in blocks[i][1] or ('伦理的' in blocks[i][1] and len(blocks[i][1]) < 200):
        show(i, '申辩篇首候选')
        break
show(0, '首块')
# 3.json 尾部(612-616) 与 4.json 开头
show(611, '3.json 倒数第3块')
show(612, '3.json 尾块')
show(613, '4.json 首块')
show(644, '4.json 块644')
show(656, '4.json 块656')
show(657, '4.json 块657')
show(690, '4.json 块690')
show(691, '4.json 块691')
show(705, '4.json 块705')
show(706, '4.json 块706')
show(803, '4.json 尾块')
