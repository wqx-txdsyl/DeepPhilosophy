# -*- coding: utf-8 -*-
"""霍布斯 (dd75d637a2ad) 章边界修正重建（2026-08-09）:
根因: 原书章节连续排版不换页 —— "通过相互立约创建国家"标题行在 idx 68 页内行 17,
旧重建把 idx 67 页(含上一章续文"版《利维坦》…")误划入第二章, 导致:
  [1] 结尾残句"…撰写《论人》和拉丁文" + [2] 开头残句"版《利维坦》的时候…"
修复: 行级边界 —— [1] 收 idx 68 行 0-16, [2] 从 idx 68 行 17(标题行) 起。
另: 删除中缝竖排残字行(1-2 字纯汉字行) + 页脚页码。
"""
import json, os, re, sys, hashlib, shutil

CKPT = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json'
BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/backend'
PUBLIC = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters'
REL = '西方/托马斯·霍布斯/托马斯•霍布斯.pdf'   # 注意作者名是 U+2022 •
bid = hashlib.md5(REL.encode()).hexdigest()[:12]
assert bid == 'dd75d637a2ad', 'bid 不符: %s' % bid

# (标题, 起页, 止页, 起页行号[None=页首], 止页行数[None=全页])
SECTIONS = [
    ("序言与目录", 0, 7, None, None),
    ("霍布斯的生平", 8, 68, None, 17),          # idx 68 取行 0-16（标题行前）
    ("通过相互立约创建国家", 68, 181, 17, None),  # idx 68 从行 17(标题行) 起
    ("建议进一步阅读", 182, 195, None, None),
    ("参考文献", 196, 215, None, None),
    ("名词索引", 216, 233, None, None),
    ("英文原著", 234, 401, None, None),
]

FOOT_RE = re.compile(r'^\d{1,4}$')           # 页脚页码
GUTTER_RE = re.compile(r'^[一-龥]{1,2}$')    # 中缝竖排残字（1-2 字纯汉字行）

def main():
    ckpt = json.load(open(CKPT, encoding='utf-8'))
    ocr = ckpt.get('ocr', {}).get('西方_托马斯_霍布斯_托马斯_霍布斯.pdf', {})
    pages = {int(k): v for k, v in ocr.items() if v and v != '__FAILED__'}
    print('ckpt 页数:', len(pages), '| 覆盖范围: %d-%d' % (min(pages), max(pages)))

    def to_blocks(ch_text):
        """与 dp_pdf_import.py 一致: 按空行切块"""
        paras = [p.strip() for p in re.split(r'\n\s*\n', ch_text) if p.strip()]
        return [{'type': 'text', 'value': p} for p in paras]

    D = os.path.join(BASE, 'data', 'book_chapters', bid)
    if os.path.isdir(D):
        shutil.rmtree(D)
    os.makedirs(D)
    toc = []
    for idx, (title, ps, pe, start_line, end_n) in enumerate(SECTIONS):
        paras = []  # 每页 1 段（页间 \n\n 分隔 → to_blocks 切出每页 1 块，与全库 _xr_nl_fix 终态一致）
        for p in range(ps, pe + 1):
            txt = pages.get(p, '')
            if not txt:
                continue
            lines = [l.strip() for l in txt.split('\n') if l.strip()]
            if p == ps and start_line is not None:
                lines = lines[start_line:]
            if p == pe and end_n is not None:
                lines = lines[:end_n]
            kept = []
            for ln in lines:
                if FOOT_RE.match(ln) or GUTTER_RE.match(ln):
                    continue
                kept.append(ln)
            if kept:
                paras.append('\n'.join(kept))
        text = '\n\n'.join(paras)
        ch = {'index': idx, 'title': title, 'content': to_blocks(text)}
        json.dump(ch, open(os.path.join(D, f'{idx}.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        toc.append(title)
        print(f'  [{idx}] {title} ({len(text):>7} 字符)', flush=True)
        print(f'       开头: {text[:55].replace(chr(10), " ")}', flush=True)
        print(f'       结尾: {text[-55:].replace(chr(10), " ")}', flush=True)
    meta = {'bookId': bid, 'title': '霍布斯', 'author': '罗宾·邦斯', 'toc': toc,
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
