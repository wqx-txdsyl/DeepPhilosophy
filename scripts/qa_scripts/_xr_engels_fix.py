# -*- coding: utf-8 -*-
"""自然辩证法 aa21ac425e87 正文修复：
A. 全角［N］独立段 → 并入前段末尾（注释标记不再切开正文）
B. 断段合并：上段无句末标点 且 下段以接续字/标点开头 或 短残段 → 并入上段
C. 33/34/35 章粘连拆分：段中 `\d{1,3}［N］` 处拆成两条目（双栏合并行）
D. 33/34/35 章标题加「〔资料〕」前缀（章节文件 + meta toc）

用法: python _xr_engels_fix.py           # 预览
      python _xr_engels_fix.py --apply   # 落盘（DP backend/data 权威）
"""
import json, os, re, sys

BID = 'aa21ac425e87'
BASE = f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}'

# 接续字（句子未说完，下段是续写）
CONT = re.compile(r'^[的了而在并就又以与和或及其它们这那之於于者所把被对从向为给没不无也还其]')
PUNCT_HEAD = re.compile(r'^[，、；：]')
FN_STANDALONE = re.compile(r'^［\d+］$')          # 全角注标独立段
FN_TITLE = re.compile(r'^［[^］]{1,24}］$')        # 方括号标题段（编者拟题）
SHORT_EXCLUDE = re.compile(r'^(第\d+节$|[A-Za-z]{1,3}$|^注释[一二三四五六七八九十]+$)')
NAME_COLON = re.compile(r'^[^。！？0-9]{1,8}：$')   # "赛奇："式引语标注（不含数字，避免误伤"就排列如图10："）
NOTE_END = re.compile(r'(［[^］]*\d+[^］]*］|\[\d+\]|\(\d{1,3}\))$')   # prev 以注标结尾 → cur 是注文/新段，不合并

def is_sentence_end(s):
    return s.endswith(('。', '！', '？', '：', '；', '”', '」', '』'))

def fix_chapter(path, fname):
    """返回 (content 列表, 统计)"""
    c = json.load(open(path, encoding='utf-8'))
    content = c['content']
    stats = {'A_fn_merge': 0, 'B_break_merge': 0, 'C_split': 0, 'A_chapter_head': 0}
    samples = {'B': [], 'C': []}

    # C. 粘连拆分（先拆，避免后续合并把两条目并一起）
    # 35 章双栏合并行: '…152［14］…' 拆在 页码+［N 连接处
    # 33 章页码+时间标题粘连: '…631874年9—10月'（63 是条目页码，1874年 是下栏时间标题）
    if fname in ('33.json', '34.json', '35.json'):
        new_content = []
        for b in content:
            v = b.get('value', '') if isinstance(b, dict) else ''
            if not isinstance(v, str):
                new_content.append(b)
                continue
            # 拆分点1: 页码［N
            positions = [m.start(1) + len(m.group(1)) for m in re.finditer(r'(\d{1,3})(［\d+\])', v)]
            # 拆分点2: 页码+19xx年（仅 33/34 细目章的时间标题粘连）
            if fname != '35.json':
                positions += [m.start(1) + len(m.group(1)) for m in re.finditer(r'(\d{1,3})(?=1[89]\d{2}年)', v)]
            # 排除段首拆分点（'1874年9—10月' 的 '1' 在 pos0 会被反复拆——幂等守卫）
            positions = [p for p in positions if p > 0]
            pos = min(positions) if positions else None
            if pos is not None:
                new_content.append({'value': v[:pos]})
                new_content.append({'value': v[pos:]})
                stats['C_split'] += 1
                if len(samples['C']) < 10:
                    samples['C'].append(v[:70])
            else:
                new_content.append(b)
        content = new_content

    # A. 全角［N］独立段并入前段
    merged = []
    for b in content:
        v = b.get('value', '') if isinstance(b, dict) else ''
        if isinstance(v, str) and FN_STANDALONE.match(v.strip()):
            if merged and isinstance(merged[-1], dict) and isinstance(merged[-1].get('value', ''), str):
                merged[-1]['value'] = merged[-1]['value'].rstrip() + v.strip()
                stats['A_fn_merge'] += 1
                continue
            else:
                # 章首注标：记录待并入上一章末段（跨文件，main 处理）
                stats['A_chapter_head'] = stats.get('A_chapter_head', 0) + 1
                stats.setdefault('head_notes', []).append(v.strip())
                continue
        merged.append(b)
    content = merged

    # B. 断段合并（33/34/35 细目/索引章不参与——条目以页码结尾+时间标题段结构特殊）
    if fname in ('33.json', '34.json', '35.json'):
        return content, stats, samples
    merged = []
    for b in content:
        v = b.get('value', '') if isinstance(b, dict) else ''
        if not merged or not isinstance(v, str):
            merged.append(b)
            continue
        prev = merged[-1]
        pv = prev.get('value', '') if isinstance(prev, dict) else ''
        if not isinstance(pv, str):
            merged.append(b)
            continue
        cur = v.strip()
        prev_t = pv.rstrip()
        if (not is_sentence_end(prev_t) and cur
                and not FN_STANDALONE.match(cur)
                and not FN_TITLE.match(cur)
                and not SHORT_EXCLUDE.match(cur)
                and not NAME_COLON.match(cur)
                and not cur.startswith('［')
                and not cur.startswith('（')
                and not cur.startswith('(')
                and not cur.startswith('——')
                and not re.match(r'^\d+[．.]', cur)   # 编号列表项（1. 2. 3.）
                and not NOTE_END.search(prev_t)
                and not prev_t.endswith('）')          # 出处标注段后是新正文段
                and not re.fullmatch(r'[A-Za-z]+', prev_t)  # 索引字母段
                and not (len(prev_t) < 15 and len(cur) >= 15 and not prev_t.startswith('（')
                         and '，' not in prev_t          # 含逗号=句子残尾（'当然，这里表明，mv和'）
                         and not re.search(r'，第[\d—\-～~]+页?$', prev_t))  # 人名+页码注文引导（'耐格里，第12—13页'）
                ):
            prev['value'] = pv.rstrip() + cur
            stats['B_break_merge'] += 1
            if len(samples['B']) < 20:
                samples['B'].append((pv[-20:], cur[:20]))
        else:
            merged.append(b)
    return merged, stats, samples

def main():
    apply = '--apply' in sys.argv
    total = {'A_fn_merge': 0, 'B_break_merge': 0, 'C_split': 0, 'A_chapter_head': 0}
    all_samples = {'B': [], 'C': []}
    contents = {}   # fname -> (path, c, new_content)
    head_notes = {}  # fname -> [注标值...]

    for f in sorted(os.listdir(BASE)):
        if not f.endswith('.json') or f == 'meta.json':
            continue
        path = os.path.join(BASE, f)
        c = json.load(open(path, encoding='utf-8'))
        # D. 33/34/35 章标题加 〔资料〕
        if f in ('33.json', '34.json', '35.json') and not c.get('title', '').startswith('〔资料〕'):
            c['title'] = '〔资料〕' + c['title']
        new_content, stats, samples = fix_chapter(path, f)
        for k in total:
            total[k] += stats[k]
        all_samples['B'] += samples['B']
        all_samples['C'] += samples['C']
        if stats.get('head_notes'):
            head_notes[f] = stats['head_notes']
        contents[f] = (path, c, new_content)

    # 章首注标跨章回并：并入上一章末段（按整数编号排序！字符串排序会 10<2）
    fnames = sorted(contents, key=lambda x: int(x.split('.')[0]))
    for i, f in enumerate(fnames):
        if f in head_notes and i > 0:
            prev_path, prev_c, prev_content = contents[fnames[i - 1]]
            if prev_content and isinstance(prev_content[-1], dict) and isinstance(prev_content[-1].get('value', ''), str):
                prev_content[-1]['value'] = prev_content[-1]['value'].rstrip() + ''.join(head_notes[f])
                print(f'  章首注标 {f} {head_notes[f]} → 并入 {fnames[i-1]} 末段')

    if apply:
        for path, c, new_content in contents.values():
            c['content'] = new_content
            json.dump(c, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    print('=== 修复统计（' + ('已落盘' if apply else '预览') + '）===')
    print(f'  A 全角［N］并入前段: {total["A_fn_merge"]}')
    print(f'  B 断段合并: {total["B_break_merge"]}')
    print(f'  C 粘连拆分: {total["C_split"]}')
    print(f'  A 章首注标保留: {total.get("A_chapter_head", 0)}')

    if not apply:
        print()
        print('=== A 章首注标位置 ===')
        for s in all_samples.get('A_head', []):
            print('  ', s)
        print()
        print('=== B 断段合并样本（前 20）===')
        for tail, head in all_samples['B'][:20]:
            print(f'  …{tail} | {head}…')
        print()
        print('=== C 粘连拆分样本（前 10）===')
        for s in all_samples['C'][:10]:
            print('  ', s[:60])

    # D. meta toc 同步
    if apply:
        mpath = os.path.join(BASE, 'meta.json')
        m = json.load(open(mpath, encoding='utf-8'))
        for t in m['toc']:
            if t['index'] in (33, 34, 35) and not t['title'].startswith('〔资料〕'):
                t['title'] = '〔资料〕' + t['title']
        json.dump(m, open(mpath, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print('meta toc 已同步 〔资料〕前缀')

if __name__ == '__main__':
    main()
