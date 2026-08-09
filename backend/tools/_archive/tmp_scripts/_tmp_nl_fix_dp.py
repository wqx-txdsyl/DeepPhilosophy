# -*- coding: utf-8 -*-
"""段内 \n 修复（临时副本——针对生产真身 DeepPhilosophy 路径）：
逻辑与 scripts/qa_scripts/_xr_nl_fix.py 完全一致, 仅 PA_BC 指向生产数据。
用法: python _tmp_nl_fix_dp.py <bid> [bid...]
"""
import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

PA_BC = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters'
SKIP = {'cd1c72bf7f81'}  # 狄俄尼索斯颂歌

def is_line_style(lines):
    """行式块：短行诗（max<=20）或索引（含'/'且max<=40）"""
    if len(lines) < 3:
        return False
    lens = [len(l.strip()) for l in lines if l.strip()]
    if not lens:
        return False
    mx = max(lens)
    if mx <= 20:
        return True
    if mx <= 40 and all('/' in l for l in lines if l.strip()):
        return True
    return False

for bid in sys.argv[1:]:
    d = os.path.join(PA_BC, bid)
    if not os.path.isdir(d):
        print('无此目录:', bid)
        continue
    if bid in SKIP:
        print('%s SKIP 保留行式（诗歌）' % bid)
        continue
    total_blk = total_dd = total_nl = 0
    for f in sorted(os.listdir(d), key=lambda x: int(x[:-5]) if x.endswith('.json') and x != 'meta.json' else -1):
        if not f.endswith('.json') or f == 'meta.json':
            continue
        p = os.path.join(d, f)
        ch = json.load(open(p, encoding='utf-8'))
        out = []
        changed = False
        for b in ch.get('content', []):
            if b.get('type') != 'text' or '\n' not in b.get('value', ''):
                out.append(b)
                continue
            v = b['value']
            changed = True
            total_blk += 1
            segs = [s for s in re.split(r'\n{2,}', v)]
            for seg in segs:
                if not seg.strip():
                    continue
                lines = seg.split('\n')
                if len(lines) >= 3 and is_line_style(lines):
                    out.append({'type': 'text', 'value': seg})
                    total_nl += seg.count('\n')
                    continue
                total_dd += 1
                out.append({'type': 'text', 'value': seg.replace('\n', '')})
        if changed:
            ch['content'] = out
            json.dump(ch, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    print('%s 修复块%d 拆段%d 保留行式\n%d' % (bid, total_blk, total_dd, total_nl))
