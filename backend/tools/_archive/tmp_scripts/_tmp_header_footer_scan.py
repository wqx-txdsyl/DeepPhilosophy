# -*- coding: utf-8 -*-
"""分析会饮篇块结构: 页眉模式统计 + 页脚注释块形态"""
import json, re

P = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\book_chapters\35279e2e439d\9.json'
ch = json.load(open(P, encoding='utf-8'))
blocks = ch.get('content', [])
print('块数:', len(blocks))

# 页眉模式统计
pat_b = re.compile(r'^(\d{1,3})\n(柏拉图对话集)(.+)$')    # 页码+书名接正文
pat_b2 = re.compile(r'^(\d{1,3})\n(柏拉图对话集)\n(.+)$')  # 页码+书名独立行
pat_s = re.compile(r'^(会饮篇|会伙篇|会伙首)\n(\d{1,3})\n(.+)$')  # 篇名+页码
pat_first = re.compile(r'^会饮篇\n（或《论爱情》，伦理的）')  # 篇首页
hdr = {'B': 0, 'B2': 0, 'S': 0, 'FIRST': 0, 'OTHER': 0, 'NONE': 0}
samples = {'OTHER': [], 'NONE': []}
for i, blk in enumerate(blocks):
    v = blk.get('value', '') if isinstance(blk, dict) else ''
    lines = v.split('\n')
    head = '\n'.join(lines[:3])
    if pat_first.match(v):
        hdr['FIRST'] += 1
    elif pat_b2.match(v):
        hdr['B2'] += 1
    elif pat_b.match(v):
        hdr['B'] += 1
    elif pat_s.match(v):
        hdr['S'] += 1
    elif re.match(r'^\d{1,3}\n', v):
        hdr['OTHER'] += 1
        samples['OTHER'].append((i, lines[:3]))
    else:
        hdr['NONE'] += 1
        samples['NONE'].append((i, lines[:3]))
print('页眉模式:', hdr)
print('OTHER 样本:')
for i, l in samples['OTHER'][:8]:
    print('  块%d: %r' % (i, l))
print('NONE 样本:')
for i, l in samples['NONE'][:10]:
    print('  块%d: %r' % (i, l))

# 页脚注释统计
print('\n== 页脚 ==')
pat_note = re.compile(r'^[①-⑩①-⑩]')
stats = []
for i, blk in enumerate(blocks):
    v = blk.get('value', '') if isinstance(blk, dict) else ''
    lines = v.split('\n')
    note_idx = [j for j, ln in enumerate(lines) if pat_note.match(ln.strip())]
    if note_idx:
        first, last = note_idx[0], note_idx[-1]
        tail = len(lines) - 1 - last  # 最后一个圈号行后的行数
        # 检查圈号行之间是否有续行
        gaps = [b - a - 1 for a, b in zip(note_idx, note_idx[1:]) if b - a > 1]
        stats.append((i, first, last, tail, gaps, lines[first][:30]))
    else:
        stats.append((i, -1, -1, -1, [], ''))
n_with_note = sum(1 for s in stats if s[1] >= 0)
print('有圈号注释的块: %d / %d' % (n_with_note, len(blocks)))
for i, first, last, tail, gaps, head_txt in stats:
    if first >= 0:
        print('  块%d: 注释行[%d-%d] 尾随%d行 间隔%s | %r' % (i, first, last, tail, gaps, head_txt))
# 无注释块样本(看尾行特征)
no_note = [(i, stats[i][0]) for i in range(len(stats)) if stats[i][1] < 0]
print('无圈号注释的块:', no_note[:10])
for i, _ in no_note[:6]:
    v = blocks[i].get('value', '') if isinstance(blocks[i], dict) else ''
    print('  块%d 尾部: %r' % (i, v.split('\n')[-3:]))
