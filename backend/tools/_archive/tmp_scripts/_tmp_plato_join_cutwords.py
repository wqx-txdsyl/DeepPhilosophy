# -*- coding: utf-8 -*-
"""跨页断词修复: A尾字+B首字若被 jieba 判为同一词(词跨越块边界) → B首字移至A尾
验证: 拼接窗口(A尾10字+B首10字) jieba 分词, 存在覆盖边界位置的词才移动
逐字循环(上限3次, 处理2-3字断词如"处罚父|亲的事情"), 每次移动后重新验证
排除: 首尾非CJK字符; 空块; 章首块(无前块)
用法: python _tmp_plato_join_cutwords.py [BID] [--apply]  (默认 BID=柏拉图对话集)
"""
import json, re, sys, os, shutil
import jieba

BID = '35279e2e439d'
for a in sys.argv[1:]:
    if a == '--apply':
        continue
    BID = a
BASE = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy'
BDIR = BASE + r'\backend\data\book_chapters'
PDIR = BASE + r'\app\public\backend\data\book_chapters'
APPLY = '--apply' in sys.argv

CJK = re.compile(r'^[\u4e00-\u9fff\u3400-\u4dbf]$')


def boundary_split_word(a_tail_line, b_head_line):
    """A尾行+B首行拼接后, jieba 是否有词跨越边界位置"""
    w_tail = a_tail_line[-10:]
    w_head = b_head_line[:10]
    cut = len(w_tail)
    pos = 0
    for w in jieba.lcut(w_tail + w_head):
        if pos < cut < pos + len(w):
            return True
        pos += len(w)
    return False


def clean_pair(a_val, b_val):
    """返回 (新A值, 新B值, 移动次数); 只移动被 jieba 验证为跨边界词的字符"""
    a_lines = a_val.split('\n')
    b_lines = b_val.split('\n')
    moved = 0
    for _ in range(3):
        ai = len(a_lines) - 1
        while ai >= 0 and not a_lines[ai].strip():
            ai -= 1
        if ai < 0:
            break
        a_line = a_lines[ai].rstrip()
        if not a_line or not CJK.match(a_line[-1]):
            break
        bi = 0
        while bi < len(b_lines) and not b_lines[bi].strip():
            bi += 1
        if bi >= len(b_lines):
            break
        b_line = b_lines[bi]
        b_head = b_line.lstrip()
        if not b_head or not CJK.match(b_head[0]):
            break
        if not boundary_split_word(a_line, b_head):
            break
        indent = b_line[:len(b_line) - len(b_head)]
        a_lines[ai] = a_line + b_head[0]
        b_lines[bi] = indent + b_head[1:]
        moved += 1
    return '\n'.join(a_lines), '\n'.join(b_lines), moved


def chapter_count():
    mp = os.path.join(BDIR, BID, 'meta.json')
    if os.path.exists(mp):
        return json.load(open(mp, encoding='utf-8')).get('chapterCount', 0)
    return 17


total_pairs = total_moved = 0
samples = []
for c in range(chapter_count()):
    bp = os.path.join(BDIR, BID, '%d.json' % c)
    if not os.path.exists(bp):
        continue
    ch = json.load(open(bp, encoding='utf-8'))
    blocks = ch.get('content', [])
    for i in range(1, len(blocks)):
        b0, b1 = blocks[i - 1], blocks[i]
        if not isinstance(b0, dict) or not isinstance(b1, dict):
            continue
        v0, v1 = b0.get('value', ''), b1.get('value', '')
        if not v0 or not v1:
            continue
        nv0, nv1, moved = clean_pair(v0, v1)
        if moved:
            total_pairs += 1
            total_moved += moved
            b0['value'], b1['value'] = nv0, nv1
            if len(samples) < 16:
                a_tail = nv0.rstrip()[-18:]
                b_head = nv1.lstrip()[:18]
                samples.append('  块%d/%d: …%s | %s…  (移%d字)' % (i, len(blocks), a_tail, b_head, moved))
    if APPLY:
        json.dump(ch, open(bp, 'w', encoding='utf-8'), ensure_ascii=False)
        pp = os.path.join(PDIR, BID, '%d.json' % c)
        if os.path.exists(pp):
            shutil.copy2(bp, pp)
print('修复断词: %d 处, 共移动 %d 字 %s' % (total_pairs, total_moved, '已写回' if APPLY else '(dry-run)'))
for s in samples:
    print(s)
