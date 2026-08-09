# -*- coding: utf-8 -*-
"""补跑：黑格尔状态确认 + 尼采 toc 补标题"""
import json, os, re

DP = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters'

def chap_count(bid):
    return len([f for f in os.listdir(os.path.join(DP, bid)) if f.endswith('.json') and f != 'meta.json'])

# 7) 黑格尔状态确认
bid = 'bbac1be0bb4b'
m = json.load(open(os.path.join(DP, bid, 'meta.json'), encoding='utf-8'))
print('[7] 黑格尔: toc=%d 条, 文件=%d 个' % (len(m['toc']), chap_count(bid)))
for t in m['toc']:
    if t.get('index') == 0:
        print('    toc[0]:', t['title'])
# 确认删掉的 index 不在 toc 且文件不存在
for n in (40, 99, 138, 164, 399, 419, 428, 449, 100, 139, 165, 400, 420, 429, 450):
    gone_file = not os.path.exists(os.path.join(DP, bid, '%d.json' % n))
    gone_toc = all(t.get('index') != n for t in m['toc'])
    if not (gone_file and gone_toc):
        print('    未删干净: index=%d file_exists=%s toc_has=%s' % (n, not gone_file, not gone_toc))
print('    商务序 [41] 保留:', os.path.exists(os.path.join(DP, bid, '41.json')))

# 8) 尼采 toc 补标题
bid = '4cc9d23c7dbf'
m = json.load(open(os.path.join(DP, bid, 'meta.json'), encoding='utf-8'))
NEW_TITLES = {
    6: '第二章 瓦格纳与现代性',
    9: '第三章 苏格拉底与科学乐观主义',
    12: '第四章 被钉十字架的上帝',
    21: '第二章 非道德论者的道德观',
    26: '第三章 快乐的与不快乐的科学',
    30: '第四章 尼采与启蒙二重性',
    41: '第二章 谁是尼采的查拉图斯特拉形象',
    46: '第三章 权力意志',
    50: '第四章 相同者的永恒轮回',
    54: '结语 未来哲学序曲',
}
n_fixed = 0
for t in m['toc']:
    n = t.get('index')
    if n in NEW_TITLES and t.get('title') != NEW_TITLES[n]:
        print('[8] 尼采 toc[%d]: %s -> %s' % (n, t['title'], NEW_TITLES[n]))
        t['title'] = NEW_TITLES[n]
        n_fixed += 1
json.dump(m, open(os.path.join(DP, bid, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('[8] 尼采: 补 %d 处（若 0 处说明已修过）' % n_fixed)
