# -*- coding: utf-8 -*-
"""柏拉图章15/16边界补丁: 从已写的新章节文件恢复原块流, 重新切分
原块序(15.json=692-705, 16.json=706-803):
  新章15 = 693..707 = 15.json[1:] + 16.json[:2]
  新章16 = 692 + 708..803 = [15.json[0]] + 16.json[2:]
"""
import json, os

B = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy'
CD = B + r'\backend\data\book_chapters\35279e2e439d'
PD = B + r'\app\public\backend\data\book_chapters\35279e2e439d'

def blocks_of(i):
    ch = json.load(open(os.path.join(CD, '%d.json' % i), encoding='utf-8'))
    return ch['content']

# 原块流 692-803
old15 = blocks_of(15)   # 692..705
old16 = blocks_of(16)   # 706..803
print('15.json 块数:', len(old15), '| 16.json 块数:', len(old16), '(应 14/98)')

new15 = old15[1:] + old16[:2]     # 693..707
new16 = [old15[0]] + old16[2:]    # 692, 708..803

print('新章15 块数:', len(new15), '首块:', new15[0]['value'][:50].replace('\n', '⏎'))
print('新章16 块数:', len(new16), '首块:', new16[0]['value'][:50].replace('\n', '⏎'))

# 写回双端
for ci, content in ((15, new15), (16, new16)):
    ch = {'title': ('柏拉图关于“是”的学说' if ci == 15 else '王太庆论柏拉图哲学和翻译问题'),
          'content': content}
    for d in (CD, PD):
        json.dump(ch, open(os.path.join(d, '%d.json' % ci), 'w', encoding='utf-8'), ensure_ascii=False)

# 校验: 首块内容
for ci in (15, 16):
    ch = json.load(open(os.path.join(CD, '%d.json' % ci), encoding='utf-8'))
    total = sum(len(b.get('value', '')) for b in ch['content'])
    print('章%d %s: %d 块, %d 字符' % (ci, ch['title'], len(ch['content']), total))
    print('  首块: %s' % ch['content'][0]['value'][:80].replace('\n', '⏎'))
    print('  尾块: %s' % ch['content'][-1]['value'][:80].replace('\n', '⏎'))
