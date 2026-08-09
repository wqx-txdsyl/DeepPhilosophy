# -*- coding: utf-8 -*-
"""全书段内 \n 修复（2026-08-09 扫描 39 本）：
- 块含 \n\n+（段落分隔）→ 按 \n\n 拆成独立 text 块（toc 均为纯 chapter 索引无 sec 锚点，拆块安全）
- 块内单 \n：行式块（诗/偈语 max行<=20，或索引 含'/'且max<=40）→ 保留行式；散文物理行 → 清 \n
- skip 白名单：cd1c72bf7f81 狄俄尼索斯颂歌（尼采诗作，行式为诗歌本体，整本不动）
用法: python _xr_nl_fix.py <bid> [bid...]
"""
import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

PA_BC = 'f:/program/Python/PhiAgent/backend/data/book_chapters'
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
    # 索引条目式：每行都含 '/'（"A/B，C" 式），避免分数斜杠（4/5）误判
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
            # 段落组：\n\n+ 分隔
            segs = [s for s in re.split(r'\n{2,}', v)]
            for seg in segs:
                if not seg.strip():
                    continue
                lines = seg.split('\n')
                if len(lines) >= 3 and is_line_style(lines):
                    out.append({'type': 'text', 'value': seg})  # 行式保留
                    total_nl += seg.count('\n')
                    continue
                total_dd += 1
                out.append({'type': 'text', 'value': seg.replace('\n', '')})
        if changed:
            ch['content'] = out
            json.dump(ch, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    print('%s 修复块%d 拆段%d 保留行式\n%d' % (bid, total_blk, total_dd, total_nl))
