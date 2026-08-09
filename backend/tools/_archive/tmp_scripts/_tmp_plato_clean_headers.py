# -*- coding: utf-8 -*-
"""柏拉图对话集 17 章页眉页脚清洗（默认 dry-run 打印统计与样本；--apply 写回双端）
页眉规则:
  A 偶数页: 块首 页码行(1-3位纯数字) → 删; 其后行若以页眉词开头 → 剥离前缀(独立行则整删)
  B 奇数页: 块首 页眉词行 + 页码行 → 删两行
  C 篇首页(无页码) 天然不匹配, 保留
页脚规则:
  D 块内第一个 ^[①-⑩] 圈号行 → 该行至块尾全删(注释块恒在页尾)
"""
import json, re, sys, os, shutil

BID = '35279e2e439d'
BASE = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy'
BDIR = BASE + r'\backend\data\book_chapters'
PDIR = BASE + r'\app\public\backend\data\book_chapters'
APPLY = '--apply' in sys.argv

HEADER_WORDS = [
    '柏拉图对话集', '拍拉图对话集',
    '欧梯甫戎篇', '欧悌甫戎篇', '苏格拉底的申辩篇', '苏格拉底的申解篇', '苏格拉底的申瓣篇',
    '格黎东篇', '卡尔弥德篇', '卡尔弥德', '拉刻篇', '吕锡篇', '吕锡',
    '枚农篇', '枚农', '裴洞篇', '装洞篇', '裴涧篇', '裴洞算', '裴润筒', '裴润简', '裴润篇', '装润篇',
    '会饮篇', '会伙篇', '会伙首', '会饮箱', '会饮简',
    '治国篇', '治国算', '治国简', '治国首',
    '巴门尼德篇', '巴门尼德算', '智者篇', '智者简',
    '苏格拉底、柏拉图传', '亚里士多德论柏拉图',
    '柏拉图关于“是”的学说', '王太庆论柏拉图哲学和翻译问题', '王太庆论柏拉图暂学和翻译问题',
    '希腊哲学术语的翻译问题', '论翻译之为再创造', '希腊专名的译法', '学和思',
    '附录', '附',
]
# 最长优先剥离
HWORDS_SORTED = sorted(HEADER_WORDS, key=len, reverse=True)
# 无页码同行剥离仅限短词(≤6字): 长词(章标题如"苏格拉底、柏拉图传")不能剥
SHORT_WORDS = [w for w in HEADER_WORDS if len(w) <= 6]
SHORT_SORTED = sorted(SHORT_WORDS, key=len, reverse=True)
PAT_PAGE = re.compile(r'^\d{1,4}(\.\d)?$')
PAT_S = re.compile(r'^(%s)\n(\d{1,4}(\.\d)?)\n' % '|'.join(map(re.escape, HEADER_WORDS)))
PAT_NOTE = re.compile(r'^[①-⑩]')

def clean_value(v):
    lines = str(v).split('\n')
    orig_len = len(lines)
    # A. 页码行(可连续: 罕见双行页眉); 页码行后行: 页眉词独立行整删 / 同行剥离
    while lines and PAT_PAGE.match(lines[0].strip()):
        lines = lines[1:]
        if not lines:
            break
        for w in HWORDS_SORTED:
            if lines[0].startswith(w):
                rest = lines[0][len(w):]
                lines = lines[1:] if not rest.strip() else [rest] + lines[1:]
                break
        break
    # B. 篇名+页码
    m = PAT_S.match(str(v))
    if m and lines:
        lines = lines[2:]
    # C. 无页码同行页眉(OCR 丢页码): 仅短词剥离, 防误伤章标题/篇首页
    #    (剥离后剩余 <4 字视为篇首页如"卡尔弥德篇"→"篇", 放弃)
    elif lines and not PAT_PAGE.match(lines[0].strip()):
        for w in SHORT_SORTED:
            if lines[0].startswith(w) and lines[0] != w and len(lines[0]) - len(w) >= 4:
                lines[0] = lines[0][len(w):]
                break
    # D. 页脚圈号注释(页尾块)
    for i, ln in enumerate(lines):
        if PAT_NOTE.match(ln.strip()):
            lines = lines[:i]
            break
    new = '\n'.join(lines)
    return new, orig_len != len(lines)

def process(path):
    ch = json.load(open(path, encoding='utf-8'))
    cnt = 0
    samples = []
    for blk in ch.get('content', []):
        if not isinstance(blk, dict) or 'value' not in blk:
            continue
        new, changed = clean_value(blk['value'])
        if changed:
            blk['value'] = new
            cnt += 1
            if len(samples) < 2:
                samples.append((blk['value'][:70],))
    return ch, cnt, samples

total_blocks = total_changed = 0
for c in range(17):
    bp = os.path.join(BDIR, BID, '%d.json' % c)
    if not os.path.exists(bp):
        continue
    pp = os.path.join(PDIR, BID, '%d.json' % c)
    ch, cnt, samples = process(bp)
    blocks = len(ch.get('content', []))
    total_blocks += blocks
    total_changed += cnt
    print('章%d: %d 块, %d 块清洗' % (c, blocks, cnt))
    for s in samples:
        print('   样本: %s' % s[0][:60])
    if APPLY:
        json.dump(ch, open(bp, 'w', encoding='utf-8'), ensure_ascii=False)
        if os.path.exists(pp):
            shutil.copy2(bp, pp)
print('\n共 %d 块, %d 块清洗 %s' % (total_blocks, total_changed, '已写回' if APPLY else '(dry-run, 加 --apply 写回)'))
