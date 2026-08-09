# -*- coding: utf-8 -*-
"""路德维希·费尔巴哈和德国古典哲学的终结（恩格斯）重建 v2：OCR 原始页 → 10 章
v2 修复（对照核查清单人工重查）:
  1. 页 42 顶部第三章尾段（'四' 行之前）混入第四章 → 移回章4末尾
  2. 普列汉诺夫《第二版序言》= PDF 86-109 独立成章（目录未列的附录，原混入人名索引）
  3. 页 82/85 版权页（ISBN 7-01-000674-1）+ 83/84 失败页丢弃
  4. 第二版序页眉（序题/栏标'普列汉诺夫…选集（第三卷）'残体）清洗
  5. 落款 '一九五年七月四日' → '一九〇五年七月四日'
  6. 页 6 竖排落款错序 → '中共中央马克思恩格斯列宁斯大林著作编译局'
  7. 页 68 版本注记两栏交错重组
- 目录锚点（书内页 = PDF页 - 9 验证全对）：编辑说明@6、1888序言@12、正文一@14、二@24、三@34、
  四@42、提纲@61、注释@69、人名索引@75（75-81）、第二版序@86（86-109）
- 清洗：页尾页码行 / __FAILED__ / 各章起始页标题行 / 正文区章序号行(^[一二三四]$)
- 提纲区(61-68)序号行保留（条目号）；正文区/第二版序 reflow；索引区行式保留
"""
import json, os, re, shutil

bid = '3a23c3ec0466'
CK = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
OUT = os.path.dirname(os.path.abspath(__file__))
SAFE = '西方_弗里德里希_恩格斯_路德维希_费尔巴哈和德国古典哲学的终结.pdf'

ck = json.load(open(CK, encoding='utf-8'))
pages = dict(ck['ocr'][SAFE])

# ── 页级预处理（整页修复）──
# 页 6：竖排落款错序（OCR 行序 马/中/著/列 → 正确 中/马/列/著）
pages['6'] = pages['6'].replace(
    '马克思恩格斯\n中共中央\n著作编译局\n列宁斯大林',
    '中共中央马克思恩格斯列宁斯大林著作编译局')
# 页 68：版本注记两栏交错 → 重组（删页码 59）
t68 = pages['68']
idx = t68.index('写于1845年春')
t68_new = (t68[:idx]
           + '写于1845年春\n原文是德文\n'
           + '第一次作为附录发表于《路德维希·费尔巴哈和德国古典哲学的终结》1888年版单行本\n'
           + '选自《马克思恩格斯选集》中文第2版第1卷第54-61页')
pages['68'] = t68_new
# 页 109：落款补〇（一九〇五年七月四日）
pages['109'] = pages['109'].replace('一九五年七月四日', '一九〇五年七月四日')

CH = {
    6: '编辑说明', 12: '1888年单行本序言',
    14: '一', 24: '二', 34: '三', 42: '四',
    61: '马克思：关于费尔巴哈的提纲', 69: '注释', 75: '人名索引',
    86: '附录：普列汉诺夫《路德维希·费尔巴哈和德国古典哲学的终结》第二版序言',
}
STRIP = {
    6: ['编辑说明'], 12: ['1888年单行本序言'],
    14: ['路德维希·费尔巴哈', '和德国古典哲学的终结'],
    61: ['马克思', '关于费尔巴哈的提纲', '1关于费尔巴哈?'],
    69: ['注释'], 75: ['人名索引'],
    86: ['[恩格斯《费尔巴哈与德国古典', '哲学的終結》一书俄澤本', '第二版的者序言了'],
}
PAGE_NO = re.compile(r'^\d{1,4}\s*$')        # 页尾页码
CH_NUM = re.compile(r'^[一二三四]\s*$')      # 正文章序号行（一/二/三/四）
FAILED = re.compile(r'^__FAILED__\s*$')
PRE = re.compile(r'^(普列汉|管列汉|列改|答列|普列|列普)[^。！？]{0,10}选[他娘第巢浆维集].{0,6}[（(].{0,4}[）)]\s*$')  # 第二版序栏标（锚定行首，OCR残体含'集'）
SEQ_TITLE = re.compile(r'^[^。！？]{1,40}(第二版序|第二版字)[^。！？]{0,14}[！）)\]】\]]?\s*$')  # 第二版序页眉（含行尾'！'变体）

def clean_page(txt, strip, drop_chnum, is_preface):
    out = []
    for ln in txt.split('\n'):
        s = ln.strip()
        if not s or s in strip or FAILED.match(s):
            continue
        if PAGE_NO.match(s):
            continue
        if drop_chnum and CH_NUM.match(s):
            continue
        if is_preface and (SEQ_TITLE.match(s) or PRE.match(s)):
            continue
        out.append(s)
    return '\n'.join(out)

NUM_LINE = re.compile(r'^[一二三四五六七八九十百千\d]{1,3}\s*$')        # 独立编号行（提纲条目）
ENTRY = re.compile(r'^（[一二三四五六七八九十百千\d]{1,3}[)）]')
MARK = re.compile(r'^(反之|答\s*[：:]?|回答\s*[：:]?|释难[一二三四五六七八九十]?|第[一二三]个问题)')

def reflow(text):
    out, buf = [], ''
    for ln in text.split('\n'):
        s = ln.strip()
        if not s:
            if buf:
                out.append(buf)
                buf = ''
            continue
        if not re.search(r'[一-鿿]', s):            # 拉丁文/纯符号行独立成段
            if buf:
                out.append(buf)
                buf = ''
            out.append(s)
            continue
        if s[0] in '*△':                            # 脚注行独立成段
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

clean = {}
for k in sorted(pages, key=int):
    k = int(k)
    if k in (0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 82, 83, 84, 85):
        continue  # 封面/失败页/目录/题名页/版权页(82,85)/失败页(83,84)
    t = clean_page(pages[str(k)], STRIP.get(k, []), 12 <= k <= 60, 86 <= k <= 109)
    if t.strip():
        clean[k] = t

order = sorted(CH)
maxp = max(clean) + 1
chapters, chapter_titles = [], []
for i, k in enumerate(order):
    end = order[i + 1] if i + 1 < len(order) else maxp
    parts = [clean[j] for j in range(k, end) if j in clean]
    if k <= 74 or k >= 86:  # 编辑说明~注释/第二版序 reflow；人名索引行式保留
        text = reflow('\n'.join(parts))
    else:
        text = '\n'.join(parts)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    chapters.append({'index': i, 'title': CH[k],
                     'content': [{'type': 'text', 'value': text}]})
    chapter_titles.append(CH[k])
    print('章%d %s: %d 字' % (i, CH[k][:30], len(text)))

# ── 页42 切分修复：'四' 行之前的第三章尾段移回章4(三) ──
TAIL3 = '就必须把这些人作为在历史中行动的人去考察。'
ch4, ch5 = chapters[4], chapters[5]
v5 = ch5['content'][0]['value'].split('\n\n')
moved = []
rest = []
for p in v5:
    if p.startswith(TAIL3):
        moved.append(p)
    else:
        rest.append(p)
if moved:
    ch4['content'][0]['value'] = (ch4['content'][0]['value'].rstrip()
                                  + '\n\n' + '\n\n'.join(moved))
    ch5['content'][0]['value'] = '\n\n'.join(rest)
    print('✓ 页42 切分: 第三章尾段 %d 段移回章4' % len(moved))
else:
    print('⚠ 页42 尾段未找到（检查 TAIL3）')

outdir = os.path.join(OUT, '_xr_out_fehb')
shutil.rmtree(outdir, ignore_errors=True)
os.makedirs(outdir, exist_ok=True)
for i, ch in enumerate(chapters):
    json.dump(ch, open(os.path.join(outdir, '%d.json' % i), 'w', encoding='utf-8'), ensure_ascii=False)
toc = [{'type': 'chapter', 'title': t, 'index': i, 'level': 1}
       for i, t in enumerate(chapter_titles)]
meta = {'bookId': bid, 'title': '路德维希·费尔巴哈和德国古典哲学的终结',
        'author': '弗里德里希·恩格斯', 'toc': toc, 'cover': '/covers/%s_cover.webp' % bid,
        'chapterCount': len(chapters), 'chapterTitles': chapter_titles}
json.dump(meta, open(os.path.join(outdir, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('输出 %d 章 + meta → %s' % (len(chapters), outdir))
