# -*- coding: utf-8 -*-
"""狄俄尼索斯颂歌（尼采，孟明译）重建：OCR 原始页 → 16 章
- 目录锚点（PDF页 = 书内页 + 9，全部验证吻合；目录两处 OCR 漏'1'：63→163、83→183）:
  10 尼采与思想之诗（孟明）@1 / 125 尼采的诗（柯利）@116 / 130 尼采的《狄俄尼索斯颂歌》（皮茨）@121 /
  140 疯子也已！诗人也已！@131 / 152 在荒原女之乡@143 / 172 最后的愿望@163 / 176 猛禽之间@167 /
  188 火符@179 / 192 太阳沉落了@183 / 200 阿莉阿德尼的咏叹@191 / 212 声名与永恒@203 /
  224 论最富者之贫@215 / 238 附录一@229 / 328 附录二@319 / 343 附录三@334 / 370 附录四@361
- 页眉规律：奇数页首行=章名（起始页同 STRIP 删）、偶数页首行=书内页码（^\d{1,4}$）；
  附录区偶数页页眉=书名残体'狄俄尼索斯项歌'、奇数页=附录标题
- 正文 9 首+附录一二为诗歌/对照（行式保留不 reflow）；前言/导读/附录三四为散文（reflow）
- 页 0-7 封面版权、8-9 目录、376 扫描信息页丢弃
"""
import json, os, re, shutil

bid = 'cd1c72bf7f81'
CK = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
OUT = os.path.dirname(os.path.abspath(__file__))
SAFE = '西方_弗里德里希_尼采_狄俄尼索斯颂歌.pdf'

ck = json.load(open(CK, encoding='utf-8'))
pages = ck['ocr'][SAFE]

CH = {
    10: '孟明：尼采与思想之诗', 125: '柯利：尼采的诗',
    130: '皮茨：尼采的《狄俄尼索斯颂歌》',
    140: '疯子也已！诗人也已！', 152: '在荒原女之乡', 172: '最后的愿望',
    176: '猛禽之间', 188: '火符', 192: '太阳沉落了', 200: '阿莉阿德尼的咏叹',
    212: '声名与永恒', 224: '论最富者之贫',
    238: '附录一、狄俄尼索斯颂歌手稿残篇', 328: '附录二、相关手稿附编',
    343: '附录三、狄俄尼索斯世界观', 370: '附录四、关于版本的说明',
}
STRIP = {
    10: ['尼采与思想之诗', '[中译本前言]', '孟明'],
    125: ['尼采的诗', '乔治·柯利'],
    130: ['尼采的《狄俄尼索斯颂歌》', '彼得·皮茨'],
    140: ['疯子也已！诗人也已！'], 152: ['在荒原女之乡'], 172: ['最后的愿望'],
    176: ['猛禽之间'], 188: ['火符'], 192: ['太阳沉落了'], 200: ['阿莉阿德尼的咏叹'],
    212: ['声名与永恒'], 224: ['论最富者之贫'],
    238: ['附录一', '狄俄尼索斯颂歌手稿残篇'],
    328: ['附录二', '相关手稿附编'],
    343: ['附录三', '狄俄尼索斯的世界观', '尼采'],
    370: ['附录四', '关于版本的说明'],
}
PAGE_NO = re.compile(r'^\d{1,4}\s*$')                 # 偶数页页码
FAILED = re.compile(r'^__FAILED__\s*$')
TITLE_H = re.compile(r'^狄俄尼索斯(颂歌|项歌|领歌)\s*$')  # 偶数页页眉（书名，含 OCR 残体）
APP_H = re.compile(r'^附录[一二三四][^。！？]{0,12}$')   # 附录奇数页页眉
HEADERS = set(CH.values()) | {'尼采与思想之诗', '尼采的诗', '尼采的《狄俄尼索斯颂歌》'}
HEADER_L = re.compile(r'^(尼采与思想之诗|尼采的诗|尼采的《狄俄尼索斯颂歌》'
                      r'|疯子也已！诗人也已！|在荒原女之乡|最后的愿望|猛禽之间|火符'
                      r'|太阳沉落了|阿莉阿德尼的咏叹|声名与永恒|论最富者之贫)\s*$')

def clean(txt, strip):
    out = []
    for ln in txt.split('\n'):
        s = ln.strip()
        if not s or s in strip or FAILED.match(s):
            continue
        if PAGE_NO.match(s) or TITLE_H.match(s) or APP_H.match(s) or HEADER_L.match(s):
            continue
        out.append(s)
    return '\n'.join(out)

NUM_LINE = re.compile(r'^[一二三四五六七八九十百千\d]{1,3}\s*$')
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
        if not re.search(r'[一-鿿]', s):
            if buf:
                out.append(buf)
                buf = ''
            out.append(s)
            continue
        if s[0] in '*△':
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

clean_pages = {}
for k in sorted(pages, key=int):
    k = int(k)
    if k < 10 or k in (376,):
        continue  # 封面/版权(0-7)/目录(8-9)/扫描信息页(376)
    t = clean(pages[str(k)], STRIP.get(k, []))
    if t.strip():
        clean_pages[k] = t

order = sorted(CH)
maxp = max(clean_pages) + 1
chapters, chapter_titles = [], []
for i, k in enumerate(order):
    end = order[i + 1] if i + 1 < len(order) else maxp
    parts = [clean_pages[j] for j in range(k, end) if j in clean_pages]
    if k < 140 or 238 <= k < 343:   # 诗歌/对照区：行式保留
        text = '\n'.join(parts)
    else:                            # 散文区：reflow
        text = reflow('\n'.join(parts))
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    chapters.append({'index': i, 'title': CH[k],
                     'content': [{'type': 'text', 'value': text}]})
    chapter_titles.append(CH[k])
    print('章%d %s: %d 字' % (i, CH[k][:25], len(text)))

outdir = os.path.join(OUT, '_xr_out_dionysos')
shutil.rmtree(outdir, ignore_errors=True)
os.makedirs(outdir, exist_ok=True)
for i, ch in enumerate(chapters):
    json.dump(ch, open(os.path.join(outdir, '%d.json' % i), 'w', encoding='utf-8'), ensure_ascii=False)
toc = [{'type': 'chapter', 'title': t, 'index': i, 'level': 1}
       for i, t in enumerate(chapter_titles)]
meta = {'bookId': bid, 'title': '狄俄尼索斯颂歌',
        'author': '弗里德里希·尼采', 'toc': toc, 'cover': '/covers/%s_cover.webp' % bid,
        'chapterCount': len(chapters), 'chapterTitles': chapter_titles}
json.dump(meta, open(os.path.join(outdir, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('输出 %d 章 + meta → %s' % (len(chapters), outdir))
