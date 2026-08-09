# -*- coding: utf-8 -*-
"""读《资本论》(b3219ec260ed) 真实章节重建（2026-08-09）:
根因: chapterize 把目录页(80-81)条目当章标题 → 前 13 章空壳。
版面: 章标题在页内(标题行前是上一章续文) → 行级切分;
      注释为页脚"（56]"式编号, 连续≥3 行成块归章尾。
"""
import json, os, re, hashlib, shutil

CKPT = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json'
BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/backend'
PUBLIC = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters'
REL = '西方/路易·阿尔都塞/读《资本论》.pdf'
bid = hashlib.md5(REL.encode()).hexdigest()[:12]
assert bid == 'b3219ec260ed', 'bid 不符: %s' % bid
SAFE = re.sub(r'[^\w\-.]', '_', REL)

# (标题, 起页, 止页, 是否目录章)
SECTIONS = [
    ("封面与版权", 0, 1, False),
    ("致读者", 2, 3, False),
    ("从《资本论》到马克思的哲学", 4, 79, False),
    ("目录", 80, 81, True),
    ("《资本论》的对象", 82, 88, False),
    ("马克思和他的发现", 89, 93, False),
    ("古典经济学的功绩", 94, 103, False),
    ("古典经济学的缺陷", 104, 138, False),
    ("马克思主义不是历史主义", 139, 170, False),
    ("《资本论》的认识论命题", 171, 186, False),
    ("政治经济学的对象", 187, 195, False),
    ("马克思的批判", 196, 215, False),
    ("马克思的巨大的理论革命", 216, 240, False),
    ("附录：关于理想的平均形式和过渡形式", 241, 247, False),
    ("关于历史唯物主义的基本概念", 248, 258, False),
    ("关于生产方式的分期", 259, 280, False),
    ("结构的各个要素及其历史", 281, 317, False),
    ("关于再生产", 318, 342, False),
    ("过渡理论的要素", 343, 388, False),
]

FOOT_RE = re.compile(r'^\d{1,4}$')            # 页码
GUTTER_RE = re.compile(r'^[一-龥A-Za-z]{1,2}$')  # 中缝/残字单行(含 V D 口)
NOISE_RE = re.compile(r'^[\s+·•.,;:，。、~—…·※]+$')
TIT_RE = re.compile(r'^[一二三四五六七八九十]{1,2}、')  # 章标题行
NOTE2_RE = re.compile(r'^[(（]\d{1,3}[\]）]')  # 页脚注释 "（56]"
PAGENUM_RE = re.compile(r'^[(（]?\d{1,4}[)）]?$')  # 目录页码行 "(77)"
AT_RE = re.compile(r'@')
END_PARA_RE = re.compile(r'[\d。！？；：…~"”』」）】%.,;:!?]$')
HEADER_WORDS = {'读《资本论》', '从《资本论》到马克思的哲学', '关于历史唯物主义的基本概念',
                '资本论》的对象', '附录：关子理想的平均形式"和过渡形式'}

def main():
    ckpt = json.load(open(CKPT, encoding='utf-8'))
    ocr = ckpt.get('ocr', {}).get(SAFE, {})
    pages = {int(k): v for k, v in ocr.items() if v and v != '__FAILED__'}
    print('ckpt 页数:', len(pages), '| 覆盖: %d-%d' % (min(pages), max(pages)))

    def plines(p):
        v = pages.get(p, '')
        return [l.strip() for l in v.split('\n') if l.strip()] if v else []

    # 预扫: 正文章起页的标题行号(切分行)
    cut = {}
    for title, ps, pe, is_toc in SECTIONS:
        if is_toc or ps == 0:
            continue
        for i, ln in enumerate(plines(ps)):
            if TIT_RE.match(ln):
                cut[ps] = i
                break
    print('切分行:', {k: v for k, v in sorted(cut.items())})

    # 页行流处理: 返回 (正文行, 注释块列表)
    def process(lines, is_toc):
        body, notes = [], []
        i = 0
        while i < len(lines):
            ln = lines[i]
            if ln in HEADER_WORDS or (not is_toc and GUTTER_RE.match(ln)):
                i += 1
                continue
            if FOOT_RE.match(ln) or PAGENUM_RE.match(ln):
                i += 1
                continue
            if NOTE2_RE.match(ln):
                # 连续注释行 ≥3 → 注释块
                block = [ln]
                j = i + 1
                while j < len(lines) and NOTE2_RE.match(lines[j]):
                    block.append(lines[j])
                    j += 1
                if len(block) >= 3:
                    notes.append('\n'.join(block))
                    i = j
                    continue
                # <3 行按正文
            ln = AT_RE.sub('', ln)
            if NOISE_RE.match(ln) or not ln:
                i += 1
                continue
            body.append(ln)
            i += 1
        return body, notes

    D = os.path.join(BASE, 'data', 'book_chapters', bid)
    if os.path.isdir(D):
        shutil.rmtree(D)
    os.makedirs(D)
    toc = []
    for idx, (title, ps, pe, is_toc) in enumerate(SECTIONS):
        if is_toc:
            # 目录章: 逐行独立块
            merged = []
            for p in range(ps, pe + 1):
                lines = plines(p)
                for ln in lines:
                    if ln in HEADER_WORDS or GUTTER_RE.match(ln):
                        continue
                    if FOOT_RE.match(ln) or PAGENUM_RE.match(ln) or NOISE_RE.match(ln):
                        continue
                    merged.append(AT_RE.sub('', ln))
        else:
            page_paras = []
            notes = []
            # 起页: 从标题行起(标题行保留)
            k = cut.get(ps, 0)
            b, n = process(plines(ps)[k:], False)
            if b:
                page_paras.append('\n'.join(b))
            notes.extend(n)
            for p in range(ps + 1, pe + 1):
                b, n = process(plines(p), False)
                if b:
                    page_paras.append('\n'.join(b))
                notes.extend(n)
            # 下一章起页的标题行前续文(仅正文邻章)
            nxt = pe + 1
            nxt_k = cut.get(nxt)
            if nxt_k is not None and nxt_k > 0:
                b, n = process(plines(nxt)[:nxt_k], False)
                if b:
                    page_paras.append('\n'.join(b))
            merged = []
            for seg in page_paras:
                if merged and not END_PARA_RE.search(merged[-1]):
                    merged[-1] += seg
                else:
                    merged.append(seg)
            merged.extend(notes)
        text = '\n\n'.join(merged)
        ch = {'index': idx, 'title': title, 'content': [{'type': 'text', 'value': v} for v in
              [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]]}
        json.dump(ch, open(os.path.join(D, '%d.json' % idx), 'w', encoding='utf-8'), ensure_ascii=False)
        toc.append(title)
        print('[%02d] %-16s %7d | %s' % (idx, title[:16], len(text), text[:40].replace('\n', ' ')), flush=True)
    meta = {'bookId': bid, 'title': '读《资本论》', 'author': '路易·阿尔都塞', 'toc': toc,
            'cover': None, 'chapterCount': len(toc), 'chapterTitles': toc}
    json.dump(meta, open(os.path.join(D, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('已重建:', bid, '|', len(toc), '章', flush=True)

    dst = os.path.join(PUBLIC, bid)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(D, dst)
    print('public 双写完成', flush=True)

if __name__ == '__main__':
    main()
