# -*- coding: utf-8 -*-
"""边沁 (74ee21ced920) 真实章节重建（2026-08-09）:
根因: chapterize 强模式把总目录页条目当章节标题, 切出 146 假章;
      原书"正文+页边章内目录"双栏混排, 目录条目行混入正文流。
修复: 总目录页码定位 20 个真实章节 SECTIONS; 行级清理
      (页码/页眉/中缝残字/孤立数字/纯目录条目行); 跨页段落合并;
      章尾脚注区; 总目录章逐行独立块。
"""
import json, os, re, hashlib, shutil

CKPT = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json'
BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/backend'
PUBLIC = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters'
REL = '西方/杰里米·边沁/道德与立法原理导论.pdf'
bid = hashlib.md5(REL.encode()).hexdigest()[:12]
assert bid == '74ee21ced920', 'bid 不符: %s' % bid

# (标题, 起页, 止页)
SECTIONS = [
    ("总目录", 0, 28),
    ("导言", 29, 84),
    ("第一章 功利原理", 85, 91),
    ("第二章 与功利原理相反的原理", 92, 108),
    ("第三章 快乐和痛苦的四种约束力或四种来源", 109, 113),
    ("第四章 如何估算快乐和痛苦的值", 114, 117),
    ("第五章 快乐和痛苦的类型", 118, 126),
    ("第六章 影响敏感性的状况", 127, 149),
    ("第七章 一般人类行动", 150, 160),
    ("第八章 意图", 161, 167),
    ("第九章 知觉", 168, 174),
    ("第十章 动机", 175, 207),
    ("第十一章 论人类的一般性情", 208, 227),
    ("第十二章 有害行动的后果", 228, 243),
    ("第十三章 不适于惩罚的情况", 244, 251),
    ("第十四章 惩罚与罪过间的比例", 252, 262),
    ("第十五章 一套惩罚所应有的特性", 263, 276),
    ("第十六章 罪过的分类", 277, 374),
    ("第十七章 刑法的界限", 375, 459),
    ("人名地名索引", 460, 468),
]
TITLE_KEY = [t.split(' ')[-1] for t, _, _ in SECTIONS]  # 页眉章名(去掉序号)

FOOT_RE = re.compile(r'^\d{1,4}$')            # 页码/孤立数字
ROMAN_RE = re.compile(r'(?i)^[ivxl]{1,8}$')   # 罗马页码(导言 xxxii 等)
GUTTER_RE = re.compile(r'^[一-龥]{1,2}$')     # 中缝残字/目、录
NOTE_RE = re.compile(r'^[①②③④⑤⑥⑦⑧⑨]')   # 脚注行
ANCHOR_RE = re.compile(r'[①②③④⑤⑥⑦⑧⑨@]+$')  # 行尾锚点(含 OCR 把②识别成@)
AT_RE = re.compile(r'@')                     # 行内锚点变体
NOISE_RE = re.compile(r'^[\s+·•.,;:，。、~—…·]+$')
DOTNUM_RE = re.compile(r'^[.．·…、]+[0-9]{1,4}$')  # 目录页码残行 "..378"
ENTRY_RE = re.compile(r'^\d+[.．、][^。！？]{1,60}$')  # 目录条目/正文条目标题
END_PARA_RE = re.compile(r'[\d。！？；：…~"”』」）】%.,;:!?]$')
HEADER_WORDS = {'道德与立法原理导论', '导言', '目', '录'}
ROMAN_PREFIX_RE = re.compile(r'^[ivxlIVXL]{1,8}\s+(?=\S)')  # 行首罗马页码前缀
CH_NUM_RE = re.compile(r'^第[一二三四五六七八九十百]+章')      # 页眉"第X章…"开头

def is_header(ln, idx):
    if ln in HEADER_WORDS:
        return True
    if idx == 0:
        return False
    title = SECTIONS[idx][0]
    if ln.replace(' ', '') == title.replace(' ', ''):
        return True
    if ln == TITLE_KEY[idx]:
        return True
    if CH_NUM_RE.match(ln) and len(ln) <= 30:
        return True
    return False

def main():
    ckpt = json.load(open(CKPT, encoding='utf-8'))
    ocr = ckpt.get('ocr', {}).get('西方_杰里米_边沁_道德与立法原理导论.pdf', {})
    pages = {int(k): v for k, v in ocr.items() if v and v != '__FAILED__'}
    print('ckpt 页数:', len(pages), '| 覆盖: %d-%d' % (min(pages), max(pages)))

    def to_blocks(ch_text):
        paras = [p.strip() for p in re.split(r'\n\s*\n', ch_text) if p.strip()]
        return [{'type': 'text', 'value': p} for p in paras]

    D = os.path.join(BASE, 'data', 'book_chapters', bid)
    if os.path.isdir(D):
        shutil.rmtree(D)
    os.makedirs(D)
    toc = []
    for idx, (title, ps, pe) in enumerate(SECTIONS):
        page_paras = []   # 每页 1 段
        notes = []
        for p in range(ps, pe + 1):
            txt = pages.get(p, '')
            if not txt:
                continue
            lines = [l.strip() for l in txt.split('\n') if l.strip()]
            body = []
            i = 0
            while i < len(lines):
                ln = lines[i]
                # 页眉章名 / 书名 / 章标题
                if is_header(ln, idx):
                    i += 1
                    continue
                if FOOT_RE.match(ln) or ROMAN_RE.match(ln) or GUTTER_RE.match(ln) or DOTNUM_RE.match(ln):
                    i += 1
                    continue
                ln = ROMAN_PREFIX_RE.sub('', ln)
                if NOTE_RE.match(ln):
                    note = [AT_RE.sub('', ln)]
                    j = i + 1
                    while j < len(lines) and not FOOT_RE.match(lines[j]) and not ROMAN_RE.match(lines[j]) and not GUTTER_RE.match(lines[j]) and not NOTE_RE.match(lines[j]):
                        note.append(AT_RE.sub('', lines[j]))
                        j += 1
                    notes.append('\n'.join(note))
                    i = j
                    continue
                ln = AT_RE.sub('', ln)
                ln = ANCHOR_RE.sub('', ln)
                if NOISE_RE.match(ln) or not ln:
                    i += 1
                    continue
                # 纯目录条目行: ^数字. 且 后跟(孤立数字行 或 连续条目行) → 删
                nxt = lines[i + 1] if i + 1 < len(lines) else ''
                if ENTRY_RE.match(ln) and (FOOT_RE.match(nxt) or ENTRY_RE.match(nxt)):
                    i += 1
                    continue
                body.append(ln)
                i += 1
            if idx == 0:
                # 总目录章: 每行独立一块（行式保留, 避免 nl_fix 散文粘连）
                page_paras.extend(body)
            else:
                if body:
                    page_paras.append('\n'.join(body))
        # 跨页合并(仅正文章; 总目录逐行)
        if idx == 0:
            merged = page_paras  # 每行=1 段
        else:
            merged = []
            for seg in page_paras:
                if merged and not END_PARA_RE.search(merged[-1]):
                    merged[-1] += seg
                else:
                    merged.append(seg)
            merged.extend(notes)
        text = '\n\n'.join(merged)
        ch = {'index': idx, 'title': title, 'content': to_blocks(text)}
        json.dump(ch, open(os.path.join(D, f'{idx}.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        toc.append(title)
        print(f'  [{idx}] {title} ({len(text):>7} 字符)', flush=True)
        print(f'       开头: {text[:50].replace(chr(10), " ")}', flush=True)
    meta = {'bookId': bid, 'title': '道德与立法原理导论', 'author': '杰里米·边沁', 'toc': toc,
            'cover': None, 'chapterCount': len(toc), 'chapterTitles': toc}
    json.dump(meta, open(os.path.join(D, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('已重建:', bid, '|', len(toc), '章', flush=True)

    os.makedirs(PUBLIC, exist_ok=True)
    dst = os.path.join(PUBLIC, bid)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(D, dst)
    print('public 双写完成', flush=True)

if __name__ == '__main__':
    main()
