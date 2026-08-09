# -*- coding: utf-8 -*-
"""通用逐行拆段修复：行级块 → 散文段落 reflow（2026-08-09 全库体检 A/B 类）
用法:
  python _xr_reflow_generic.py <bid> --chapters 51,104,8     # 点名修指定章
  python _xr_reflow_generic.py <bid> --all                    # 整本（自动跳过表格章）
  python _xr_reflow_generic.py <bid> --all --skip 12,13       # 附加排除
规则:
  标题行(章/节/part, norm 匹配)独立段; 脚注行(①②…)独立段; 无汉字行独立段;
  行尾 。！？… 断段; 空行断段; 其余行并入当前段
  非 text 块(图片等)原位保留为独立段; 重排后按标题精确匹配重算 section 锚点
  同时更新 PA book_detail 的 toc
"""
import json, os, re, sys, shutil
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PA_BC = 'f:/program/Python/PhiAgent/backend/data/book_chapters'
PA_BD = 'f:/program/Python/PhiAgent/backend/data/book_detail'
TABLE_WORDS = ['对照', '索引', '术语', '年表', '细目', '总目录', '参考书目', '词汇索引', '人名表', '缩写']
END = '。！？…'
FOOT = re.compile(r'^[①②③④⑤⑥⑦⑧⑨⑩]')
HAN = re.compile(r'[一-鿿]')

def norm(s):
    return re.sub(r'\s+', '', s or '')

def is_table_ch(title):
    return any(w in title for w in TABLE_WORDS)

def reflow_chapter(ch, titles_set):
    titles_norm = {norm(t): t for t in titles_set}
    # 1) 展开行流
    rows = []  # (kind, s) kind: line / empty / other(非text块)
    for b in ch.get('content', []):
        if b.get('type') != 'text':
            rows.append(('other', b))
            continue
        for ln in b.get('value', '').split('\n'):
            s = ln.strip()
            rows.append(('empty', '') if not s else ('line', s))
    # 2) 跨行标题组识别（≤3行拼接精确匹配, 不跨空行/其他块）
    spans = []  # (start, end, canonical)
    i, n = 0, len(rows)
    while i < n:
        if rows[i][0] != 'line':
            i += 1
            continue
        matched = None
        for k in range(3):
            if i + k >= n or rows[i + k][0] != 'line':
                break
            seg = norm(''.join(rows[i + j][1] for j in range(k + 1)))
            if seg in titles_norm:
                matched = (i, i + k + 1, titles_norm[seg])
        if matched:
            spans.append(matched)
            i = matched[1]
        else:
            i += 1
    # 3) 重排
    out, buf = [], ''
    warns = []

    def flush():
        nonlocal buf
        if buf:
            out.append({'type': 'text', 'value': buf})
            buf = ''

    pos = 0
    idx = 0
    while idx < n:
        kind, s = rows[idx]
        if pos < len(spans) and spans[pos][0] == idx:
            flush()
            out.append({'type': 'text', 'value': spans[pos][2]})
            idx = spans[pos][1]
            pos += 1
            continue
        if pos < len(spans) and spans[pos][0] < idx < spans[pos][1]:
            idx += 1
            continue
        if kind == 'other':
            flush()
            out.append(s)
            idx += 1
            continue
        if kind == 'empty':
            flush()
            idx += 1
            continue
        # line
        if FOOT.match(s):              # 脚注行独立段
            flush()
            out.append({'type': 'text', 'value': s})
            idx += 1
            continue
        if HAN.search(s):               # 中文行: 拼接, 句尾 。！？… 断段
            buf = (buf + s) if buf else s
            if s[-1] in END or (len(s) >= 2 and s[-2] in END and s[-1] in '"”』」）】'):
                flush()
            idx += 1
            continue
        if re.search(r'[A-Za-z]', s):   # 拉丁(德/英)行: 空格拼接, 句尾 .!?… 断段
            buf = (buf + ' ' + s) if buf else s
            if s[-1] in '.!?…':
                flush()
            idx += 1
            continue
        # 纯符号/数字/页码行独立段
        flush()
        out.append({'type': 'text', 'value': s})
        idx += 1
        continue
    flush()
    ch['content'] = out
    return warns

def remap_sections(meta, ch, ch_title):
    """按标题精确匹配重算 toc section 锚点; 返回警告"""
    warns = []
    titles = [t for t in meta['toc'] if t.get('type') == 'section' and t.get('index') == ch['index']]
    blocks = [b.get('value', '').strip() for b in ch['content'] if b.get('type') == 'text']
    for t in titles:
        tn = norm(t['title'])
        found = next((i for i, v in enumerate(blocks) if norm(v) == tn), -1)
        if found < 0:   # 兼容"章名·节名"前缀标题(如 尽心章句下·第三十三节)
            found = next((i for i, v in enumerate(blocks)
                          if tn and tn in norm(v)[:len(tn) + 12]), -1)
        if found >= 0:
            t['sec'] = found
        else:
            warns.append('节[%s] 章[%s] 锚点丢失' % (t['title'], ch_title))
    return warns

def main():
    bid = sys.argv[1]
    args = sys.argv[2:]
    mode_all = '--all' in args
    picks = []
    skip = set()
    for a in args:
        if a.startswith('--chapters'):
            picks = [int(x) for x in a.split('=', 1)[1].split(',') if x.strip()]
        elif a.startswith('--skip'):
            skip = {int(x) for x in a.split('=', 1)[1].split(',') if x.strip()}
    d = os.path.join(PA_BC, bid)
    meta = json.load(open(os.path.join(d, 'meta.json'), encoding='utf-8'))
    titles_set = {norm(t['title']) for t in meta['toc']} | {norm(meta.get('title', ''))}
    ch_files = sorted([f for f in os.listdir(d) if f.endswith('.json') and f != 'meta.json'],
                      key=lambda x: int(x[:-5]))
    targets = []
    for f in ch_files:
        idx = int(f[:-5])
        ch = json.load(open(os.path.join(d, f), encoding='utf-8'))
        if idx in skip:
            continue
        if picks:
            if idx in picks:
                targets.append((idx, ch, f))
            continue
        if mode_all:
            if is_table_ch(ch.get('title', '')):
                print('  跳过表格章 %d %s' % (idx, ch.get('title', '')[:24]))
                continue
            targets.append((idx, ch, f))
    if not targets:
        print('无可处理章节')
        return
    print('处理 %s 共 %d 章:' % (bid, len(targets)))
    total_warns = []
    for idx, ch, f in targets:
        before = len(ch.get('content', []))
        w = reflow_chapter(ch, titles_set)
        w += remap_sections(meta, ch, ch.get('title', ''))
        total_warns += w
        after = len(ch['content'])
        chars = sum(len(b.get('value', '')) for b in ch['content'] if b.get('type') == 'text')
        first = (ch['content'][0].get('value', '')[:18].replace('\n', ' ')
                 if ch['content'] else '')
        print('  章%d %-20s 块 %4d→%4d  %d字 首: %s' % (idx, ch.get('title', '')[:20], before, after, chars, first))
        json.dump(ch, open(os.path.join(d, f), 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(meta, open(os.path.join(d, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    # PA detail toc 同步
    df = os.path.join(PA_BD, bid + '.json')
    det = json.load(open(df, encoding='utf-8'))
    det['toc'] = meta['toc']
    det['chapterCount'] = meta['chapterCount']
    det['chapterTitles'] = meta['chapterTitles']
    json.dump(det, open(df, 'w', encoding='utf-8'), ensure_ascii=False)
    print('PA detail toc 同步 ✓')
    if total_warns:
        print('⚠ 锚点警告 %d 条:' % len(total_warns))
        for w in total_warns:
            print('  ', w)
    else:
        print('全部节锚点重算 ✓')

if __name__ == '__main__':
    main()
