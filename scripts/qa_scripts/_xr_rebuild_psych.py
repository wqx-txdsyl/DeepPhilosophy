# -*- coding: utf-8 -*-
"""从经验立场出发的心理学（弗朗茨·布伦塔诺，郝亿春译）重建：OCR 原始页 → 21 章
- 目录锚点（书内页 = PDF页 - 8，PDF18=10 验证）：
  总序@4 / 1874年版前言@9 / 1911年版前言@13 / 第一卷@15 / 第一章心理学的概念与目标@17 /
  第二章心理学方法：尤其关注其经验基础@44 / 第三章…归纳@87 / 第四章…非精确特征、演绎及确证@88 /
  第二卷@99 / 第一章心理现象与物理现象的区别@101 / 第二章内意识@127 / 第三章对内意识的进一步考察@171 /
  第四章关于意识的统一性@192 / 第五章对用以区分心理现象的原则之探究@218 /
  第六章心理活动划分为表象、判断、爱恨现象@239 / 第七章表象与判断：两种不同的基本类型@248 /
  第八章情感与意欲统合为一个基本类型@285 / 第九章三种基本类型与内意识的三重现象之比较及其自然位序的确定@319 /
  1911年版附录@324 / 中译说明@366
- 页眉体系：偶数页=页码+卷名页眉（78/第一卷作为一门科学的心理学）；奇数页=章名页眉+页码（第四章关于意识的统一性/199）；
  章首页特殊：章名跨行/页码错乱（44 首'第二章心理学方法：/28/尤其关注其经验基础'，88 首'6其…'，218 次行'177'）
- 页码 OCR 错乱（155/208/177/830/810）由行正则删除
- 页 0-3 封面/版权、7-8 目录、16/100 FAILED、368 定价页丢弃；卷首页(15/99)保留为章内容
- 全部正文散文 reflow；脚注①独立段
"""
import json, os, re, shutil

bid = '37e1e8e2842b'
CK = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
OUT = os.path.dirname(os.path.abspath(__file__))
SAFE = '西方_弗朗茨_布伦塔诺_从经验立场出发的心理学.pdf'

ck = json.load(open(CK, encoding='utf-8'))
pages = dict(ck['ocr'][SAFE])

CH = {
    4: '总序', 9: '1874年版前言', 13: '1911年版前言',
    15: '第一卷 作为一门科学的心理学',
    17: '第一章 心理学的概念与目标',
    44: '第二章 心理学方法：尤其关注其经验基础',
    87: '第三章 对心理学方法的进一步探讨：对心理学基本规律的归纳',
    88: '第四章 对心理学方法的进一步探讨：其最高规律的非精确特征、演绎及确证',
    99: '第二卷 心理现象概论',
    101: '第一章 心理现象与物理现象的区别', 127: '第二章 内意识',
    171: '第三章 对内意识的进一步考察', 192: '第四章 关于意识的统一性',
    218: '第五章 对用以区分心理现象的原则之探究',
    239: '第六章 心理活动划分为表象、判断、爱恨现象',
    248: '第七章 表象与判断：两种不同的基本类型',
    285: '第八章 情感与意欲统合为一个基本类型',
    319: '第九章 三种基本类型与内意识的三重现象之比较及其自然位序的确定',
    324: '1911年版附录', 366: '中译说明',
}
STRIP = {
    4: ['总序'], 5: ['总序'], 6: ['总', '序'],
    9: ['1874年版前言'], 10: ['1874年版前言'], 11: ['1874年版前言'], 12: ['1874年版前言'],
    13: ['1911年版前言?', '1911年版前言'], 14: ['1911年版前言'],
    17: ['第一章心理学的概念与目标'],
    44: ['第二章心理学方法：', '尤其关注其经验基础'],
    88: ['第四章对心理学方法的进一步探讨：', '6其最高规律的非精确特征、演绎及确证', '其最高规律的非精确特征、演绎及确证'],
    101: ['第一章心理现象与物理现象的区别”', '第一章心理现象与物理现象的区别'],
    127: ['第二章内意识?', '第二章内意识'],
    171: ['第三章对内意识的进一步考察'],
    192: ['第四章关于意识的统一性'],
    218: ['第五章对用以区分心理', '第五章对用以区分心理现象的原则之探究', '现象的原则之探究'],
    239: ['第六章心理活动划分为', '第六章心理活动划分为表象、判断、爱恨现象', '表象、判断、爱恨现象'],
    248: ['第七章表象与判断：', '第七章表象与判断：两种不同的基本类型', '两种不同的基本类型'],
    285: ['第八章情感与意欲', '第八章情感与意欲统合为一个基本类型', '统合为一个基本类型'],
    319: ['第九章三种基本类型与内意识的', '第九章三种基本类型与内意识的三重现象之比较及其自然位序的确定'],
    324: ['1911年版附录'],
    366: ['中译说明'], 367: ['中译说明'],
}
PAGE_NUM = re.compile(r'^\d{1,4}\s*$')                    # 页码行（阿拉伯）
ROMAN = re.compile(r'^[IVXLicvxlⅠ-Ⅻ]{1,6}\s*$')           # 页码行（罗马：Xxvii/XXV/iiI）
CH_NUM = re.compile(r'^第[一二三四五六七八九十百]+章[^。！？]{1,40}\s*$')   # 奇数页章名页眉（含截断变体）
CH_VOL = re.compile(r'^第[一二]卷[^。！？]{1,20}\s*$')       # 偶数页卷名页眉
HEADERS = {'总序', '1874年版前言', '1911年版前言', '1911年版附录', '中译说明'}
ODD_FOOT = re.compile(r'^[^。！？]{1,25}\d{2,3}\s*$')       # 章首页章名+页码同行（…归纳79/…确定315）
FAILED = re.compile(r'^__FAILED__\s*$')

def clean(txt, strip):
    out = []
    for ln in txt.split('\n'):
        s = ln.strip()
        if not s or s in strip or FAILED.match(s):
            continue
        if (PAGE_NUM.match(s) or ROMAN.match(s) or CH_NUM.match(s)
                or CH_VOL.match(s) or ODD_FOOT.match(s) or s in HEADERS):
            continue
        out.append(s)
    return '\n'.join(out)

NUM_LINE = re.compile(r'^[一二三四五六七八九十百千\d]{1,3}\s*$')
ENTRY = re.compile(r'^（[一二三四五六七八九十百千\d]{1,3}[)）]')

def reflow(text):
    out, buf = [], ''
    for ln in text.split('\n'):
        s = ln.strip()
        if not s:
            if buf:
                out.append(buf)
                buf = ''
            continue
        if not re.search(r'[一-鿿]', s):            # 拉丁/希腊文/纯符号行独立成段
            if buf:
                out.append(buf)
                buf = ''
            out.append(s)
            continue
        if s[0] in '*△①':                          # 脚注行独立成段
            if buf:
                out.append(buf)
                buf = ''
            out.append(s)
            continue
        if re.match(r'^[一二三四五六七八九十百]+、[^。！？]{1,25}$', s):   # 附录节标题（一、…）独立成段
            if buf:
                out.append(buf)
                buf = ''
            out.append(s)
            continue
        if NUM_LINE.match(s):
            if buf:
                out.append(buf)
                buf = ''
            out.append(s)
            continue
        if buf and ENTRY.match(s):
            out.append(buf)
            buf = ''
        buf = (buf + s) if buf else s
        if s[-1] in '。！？；：」』）】"':
            out.append(buf)
            buf = ''
    if buf:
        out.append(buf)
    return '\n\n'.join(out)

clean_pages = {}
for k in sorted(pages, key=int):
    k = int(k)
    if k <= 3 or 7 <= k <= 8 or k in (16, 100, 368):
        continue  # 封面/CIP/英文版权(0-3)、目录(7-8)、FAILED(16,100)、定价页(368)
    t = clean(pages[str(k)], STRIP.get(k, []))
    if t.strip():
        clean_pages[k] = t

order = sorted(CH)
maxp = max(clean_pages) + 1
chapters, chapter_titles = [], []
for i, k in enumerate(order):
    end = order[i + 1] if i + 1 < len(order) else maxp
    parts = [clean_pages[j] for j in range(k, end) if j in clean_pages]
    if k in (15, 99):          # 卷首页：行式保留（内容=卷名标题）
        text = '\n'.join(parts)
    else:                      # 其余散文区：reflow
        text = reflow('\n'.join(parts))
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    chapters.append({'index': i, 'title': CH[k],
                     'content': [{'type': 'text', 'value': text}]})
    chapter_titles.append(CH[k])
    print('章%d %s: %d 字' % (i, CH[k][:24], len(text)))

outdir = os.path.join(OUT, '_xr_out_psych')
shutil.rmtree(outdir, ignore_errors=True)
os.makedirs(outdir, exist_ok=True)
for i, ch in enumerate(chapters):
    json.dump(ch, open(os.path.join(outdir, '%d.json' % i), 'w', encoding='utf-8'), ensure_ascii=False)
toc = [{'type': 'chapter', 'title': t, 'index': i, 'level': 1}
       for i, t in enumerate(chapter_titles)]
meta = {'bookId': bid, 'title': '从经验立场出发的心理学',
        'author': '弗朗茨·布伦塔诺', 'toc': toc, 'cover': '/covers/%s_cover.webp' % bid,
        'chapterCount': len(chapters), 'chapterTitles': chapter_titles}
json.dump(meta, open(os.path.join(outdir, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('输出 %d 章 + meta → %s' % (len(chapters), outdir))
