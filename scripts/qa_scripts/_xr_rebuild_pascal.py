# -*- coding: utf-8 -*-
"""思想录（帕斯卡尔）重建：OCR 原始页 → 20 章（出版说明/译序/第一~十四编/附录一~四）
- 目录锚点（书内页 = PDF页 - 9 验证全对）：第一编@12、第二编@33、第三编@96、第四编@126、
  第五编@145、第六编@165、第七编@193、第八编@257、第九编@274、第十编@307、第十一编@337、
  第十二编@381、第十三编@408、第十四编@441、附录一@466、附录二@478、附录三@484、附录四@536
- 清洗：栏标行（手稿编号 21-910*(1)105-187，纯数字+符号无拉丁字母无中文）/ 页码行 /
  ·主题· 页眉（主题·/·主题/页码·主题/主题·页码 变体）/ 罗马页码(iv) / __FAILED__
- 拉丁文引文行（无中文含拉丁字母）保留为独立段；行内无栏标（66 处数字-数字全为注释内容）
- 年表区/索引区（附录三/四）行式保留不 reflow；正文区 reflow 段落恢复
"""
import json, os, re, shutil

bid = '9dc98919ade8'
CK = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
OUT = os.path.dirname(os.path.abspath(__file__))
SAFE = '西方_布莱兹_帕斯卡尔_思想录.pdf'

ck = json.load(open(CK, encoding='utf-8'))
pages = ck['ocr'][SAFE]

# ── 章节锚点（PDF 页）与标题（目录原文）──
CH = {
    3: '出版说明', 4: '译序',
    12: '第一编：关于精神和文风的思想', 33: '第二编：人没有上帝是可悲的',
    96: '第三编：必须打赌', 126: '第四编：信仰的手段', 145: '第五编：正义和作用的原因',
    165: '第六编：哲学家', 193: '第七编：道德和学说', 257: '第八编：基督宗教的基础',
    274: '第九编：永存性', 307: '第十编：论象征', 337: '第十一编：预言',
    381: '第十二编：对耶稣基督的证明', 408: '第十三编：奇迹', 441: '第十四编：辩驳断想',
    466: '附录一：帕斯卡尔的生平和科学贡献', 478: '附录二：有关版本和译文的一些说明',
    484: '附录三：帕斯卡尔生平和著作年表', 536: '附录四：词语对照索引',
}
# 每章起始页的标题行（删）
STRIP = {
    3: ['汉译世界学术名著丛书', '出版说明'], 4: ['译序'],
    12: ['第一编'], 33: ['第二编'], 96: ['第三编'], 126: ['第四编'], 145: ['第五编'],
    165: ['第六编'], 193: ['第七编'], 257: ['第八编'], 274: ['第九编'], 307: ['第十编'],
    337: ['第十一编'], 381: ['第十二编'], 408: ['第十三编'], 441: ['第十四编'],
    466: ['附录', '帕斯卡尔的生平和科学贡献'],
    478: ['有关版本和译文的一些说明'],
    484: ['帕斯卡尔生平和著作年表', '（1623—1662，三九岁）'],
    536: ['词语对照索引'],
}
HEADER = re.compile(r'^·[^·]{1,25}·?\s*$')           # ·主题·（正文奇页页眉）
HEADER2 = re.compile(r'^[^·]{1,25}·\s*$')             # 主题·（附录页眉）
HEADER3 = re.compile(r'^\d{1,4}·[^·]{1,25}·?\s*$')    # 页码·主题·（年表/索引页眉）
HEADER4 = re.compile(r'^[^·]{1,25}·\d{1,4}\s*$')      # 主题·页码（年表页眉）
PAGE_NO = re.compile(r'^\d{1,4}\s*$')                 # 页码行
ROMAN = re.compile(r'^[ivxlIVXL]{1,4}\s*$')           # 译序罗马页码
FAILED = re.compile(r'^__FAILED__\s*$')

def is_margin(s):
    """栏标行：含数字、无中文；剥掉变体字母(a/b)与罗马数字(L/V/XL)后仍含数字
    拉丁文引文行（纯字母无数字）不会被误判"""
    if not any(c.isdigit() for c in s):
        return False
    if re.search(r'[一-鿿]', s):
        return False
    t = re.sub(r'[a-zA-Z]', '', s)
    return bool(re.search(r'\d', t))

def clean_body(txt, strip=None):
    """正文/附录一二清洗（章0-17）"""
    strip = strip or []
    out = []
    for ln in txt.split('\n'):
        s = ln.strip()
        if not s or s in strip or FAILED.match(s):
            continue
        if ROMAN.match(s) or PAGE_NO.match(s) or HEADER.match(s) \
                or HEADER2.match(s) or HEADER3.match(s) or HEADER4.match(s) \
                or is_margin(s):
            continue
        out.append(s)
    return '\n'.join(out)

def clean_plain(txt, strip=None):
    """年表/索引区清洗（章18-19）：行式保留，只删页眉/页码/失败行"""
    strip = strip or []
    out = []
    for ln in txt.split('\n'):
        s = ln.strip()
        if not s or s in strip or FAILED.match(s):
            continue
        if PAGE_NO.match(s) or HEADER.match(s) or HEADER2.match(s) \
                or HEADER3.match(s) or HEADER4.match(s):
            continue
        out.append(s)
    return '\n'.join(out)

NUM_LINE = re.compile(r'^[一二三四五六七八九十百千\d]{1,3}\s*$')        # 独立编号行
ENTRY = re.compile(r'^（[一二三四五六七八九十百千\d]{1,3}[)）]')         # 条目"（1）…"
MARK = re.compile(r'^(反之|答\s*[：:]?|回答\s*[：:]?|释难[一二三四五六七八九十]?|第[一二三]个问题)')  # 结构标记

def reflow(text):
    """OCR 物理断行 → 段落：行尾强句读/条目结构标记断段；独立编号行与拉丁文引文行独立成段"""
    out, buf = [], ''
    for ln in text.split('\n'):
        s = ln.strip()
        if not s:
            if buf:
                out.append(buf)
                buf = ''
            continue
        if not re.search(r'[一-鿿]', s):            # 拉丁文引文/纯符号行独立成段
            if buf:
                out.append(buf)
                buf = ''
            out.append(s)
            continue
        if s[0] in '*△':                            # 脚注行（* 标记，行尾常无句读）独立成段
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

# ── 1. 逐区清洗 ──
clean = {}
for k in sorted(pages, key=int):
    k = int(k)
    if k < 3:
        continue  # 封面/版权丢弃
    if k in (8, 9, 10, 11):
        continue  # 目录页(8-9)/书名页(10)/失败页(11)
    if 3 <= k <= 465 or 466 <= k <= 483:
        t = clean_body(pages[str(k)], STRIP.get(k))
    else:
        t = clean_plain(pages[str(k)], STRIP.get(k))
    if t.strip():
        clean[k] = t

# ── 2. 切分章节 ──
order = sorted(CH)
maxp = max(clean) + 1
chapters, chapter_titles = [], []
for i, k in enumerate(order):
    end = order[i + 1] if i + 1 < len(order) else maxp
    parts = [clean[j] for j in range(k, end) if j in clean]
    if k <= 483:  # 正文/附录一二 reflow；附录三/四行式保留
        text = reflow('\n'.join(parts))
    else:
        text = '\n'.join(parts)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    chapters.append({'index': i, 'title': CH[k],
                     'content': [{'type': 'text', 'value': text}]})
    chapter_titles.append(CH[k])
    print('章%d %s: %d 字' % (i, CH[k][:20], len(text)))

outdir = os.path.join(OUT, '_xr_out_pascal')
shutil.rmtree(outdir, ignore_errors=True)  # 先清空防旧文件残留
os.makedirs(outdir, exist_ok=True)
for i, ch in enumerate(chapters):
    json.dump(ch, open(os.path.join(outdir, '%d.json' % i), 'w', encoding='utf-8'), ensure_ascii=False)
toc = [{'type': 'chapter', 'title': t, 'index': i, 'level': 1}
       for i, t in enumerate(chapter_titles)]
meta = {'bookId': bid, 'title': '思想录',
        'author': '布莱兹·帕斯卡尔', 'toc': toc, 'cover': '/covers/%s_cover.webp' % bid,
        'chapterCount': len(chapters), 'chapterTitles': chapter_titles}
json.dump(meta, open(os.path.join(outdir, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('输出 %d 章 + meta → %s' % (len(chapters), outdir))
