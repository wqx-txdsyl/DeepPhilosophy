# -*- coding: utf-8 -*-
"""新工具（培根）重建：OCR 原始页 → 3 章（序言 / 第一卷 / 第二卷）
- 页 0-4（丛书封面/版权/目录）丢弃；序言@页5、第一卷@页11、第二卷@页110
- 清洗：页码行(^\d{1,3}$) / 卷页眉(^第[一二]卷$) / 书眉(^新工具[①②]?$) / 序言标题(^序言[·.]$)
- 页10 为 __FAILED__ 空白页 → 丢弃；页11 残片行（语录?/第—卷?/第一章）删除，卷标题规范化保留
"""
import json, os, re, shutil

bid = '7bb94a203c8c'
CK = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
OUT = os.path.dirname(os.path.abspath(__file__))
SAFE = '西方_弗朗西斯_培根_新工具.pdf'

ck = json.load(open(CK, encoding='utf-8'))
pages = ck['ocr'][SAFE]

PAGE_NO = re.compile(r'^\d{1,3}\s*$')                      # 页首页码行（书内页=PDF页-4）
VOL_HDR = re.compile(r'^第[—\-一二]卷\s*$')                    # 卷页眉（偶页页眉，页109/295）
BK_HDR = re.compile(r'^新工具[①②③④⑤⑥⑦⑧]?\s*$')            # 书眉（页5'新工具①'、页294'新工具'）
PRE_TTL = re.compile(r'^序言[·.]?\s*$')                     # 序言标题行（页5'序言·'）
Q_HEAD = re.compile(r'^语录[?？]?\s*$')                     # 页11残片'语录?'
BAD_TTL = re.compile(r'^第[—\-一]卷[?？]?\s*$')               # 页11残片'第—卷?'（卷号OCR变体）
CH_ONE = re.compile(r'^第一章\s*$')                         # 页11残片（新工具无章节结构）
FAILED = re.compile(r'^__FAILED__\s*$')                     # OCR 失败残片/空白页
VOL_TTL = re.compile(r'^[一一—\-]{1,3}关于解释自然和关于人的领域[一一—\-]{1,3}\s*$')  # 卷标题（规范化保留）

def clean_page(txt):
    lines = []
    for ln in txt.split('\n'):
        s = ln.strip()
        if not s or PAGE_NO.match(s) or VOL_HDR.match(s) or BK_HDR.match(s) \
                or PRE_TTL.match(s) or Q_HEAD.match(s) or BAD_TTL.match(s) \
                or CH_ONE.match(s) or FAILED.match(s):
            continue
        if VOL_TTL.match(s):
            lines.append('关于解释自然和关于人的领域')  # 卷标题规范化
            continue
        lines.append(s)
    return '\n'.join(lines)

NUM_LINE = re.compile(r'^[一二三四五六七八九十百千\d]{1,3}\s*$')        # 独立编号行（语录"一"）
ENTRY = re.compile(r'^（[一二三四五六七八九十百千\d]{1,3}[)）]')         # 条目"（1）…"
MARK = re.compile(r'^(反之|答\s*[：:]?|回答\s*[：:]?|释难[一二三四五六七八九十]?|第[一二三]个问题)')  # 结构标记

INLINE_ALL = re.compile(r'(?<=[一-鿿])\d{3,4}[a-z]')  # 整章兜底（OCR断行拆散的数字+字母）

def reflow(text):
    """OCR 物理断行 → 段落：行尾强句读/条目结构标记断段；独立编号行保持独立"""
    out, buf = [], ''
    for ln in text.split('\n'):
        s = ln.strip()
        if not s:
            if buf:
                out.append(buf)
                buf = ''
            continue
        if NUM_LINE.match(s):
            if buf:
                out.append(buf)
                buf = ''
            out.append(s)
            continue
        if buf and (ENTRY.match(s) or MARK.match(s)):
            out.append(buf)
            buf = ''
        buf = (buf + s) if buf else s
        if s[-1] in '。！？；：」』）】"':
            out.append(buf)
            buf = ''
    if buf:
        out.append(buf)
    return '\n\n'.join(out)

clean = {}
for k in sorted(pages, key=int):
    if int(k) < 5:
        continue
    t = clean_page(pages[k])
    if t.strip():
        clean[int(k)] = t  # 清洗后为空页（如页10 __FAILED__）跳过

# 切分锚点（目录/书内页码对照：第二卷 106 书内页 = PDF 页 110）
ANCHORS = [(5, '序言'), (11, '第一卷'), (110, '第二卷')]
maxp = max(clean) + 1

chapters, chapter_titles = [], []
for i, (k, title) in enumerate(ANCHORS):
    end = ANCHORS[i + 1][0] if i + 1 < len(ANCHORS) else maxp
    parts = [clean[j] for j in range(k, end) if j in clean]
    text = INLINE_ALL.sub('', reflow('\n\n'.join(parts)))
    chapters.append({'index': i, 'title': title,
                     'content': [{'type': 'text', 'value': text}]})
    chapter_titles.append(title)
    print('章%d %s: %d 字' % (i, title, len(text)))

outdir = os.path.join(OUT, '_xr_out_bacon')
shutil.rmtree(outdir, ignore_errors=True)  # 先清空防旧文件残留
os.makedirs(outdir, exist_ok=True)
for i, ch in enumerate(chapters):
    json.dump(ch, open(os.path.join(outdir, '%d.json' % i), 'w', encoding='utf-8'), ensure_ascii=False)
toc = [{'type': 'chapter', 'title': t, 'index': i, 'level': 1}
       for i, t in enumerate(chapter_titles)]
meta = {'bookId': bid, 'title': '新工具',
        'author': '弗朗西斯·培根', 'toc': toc, 'cover': '/covers/%s_cover.webp' % bid,
        'chapterCount': len(chapters), 'chapterTitles': chapter_titles}
json.dump(meta, open(os.path.join(outdir, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('输出 %d 章 + meta → %s' % (len(chapters), outdir))
