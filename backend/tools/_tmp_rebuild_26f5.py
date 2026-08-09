# -*- coding: utf-8 -*-
"""哲学规劝录·哲学的慰藉 (26f5e0df6d76) 页级重建（2026-08-09）:
43 章自动切分 toc 垃圾（目录页 TOC 行误切 [0-17]、页眉 OCR 变体致重复章、
第二十一章吞掉附录+整本慰藉）。改为按物理页范围手工指定边界重建 34 章。
页眉清理: 带"书名|"前缀整行删; 裸章节标题行 seen-set 去重（保留首次）; 页脚页码删。
"""
import json, os, re, sys, hashlib, shutil

CKPT = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json'
BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/backend'
PUBLIC = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters'
DETAIL_DIR = os.path.join(BASE, 'data', 'book_detail')
REL = '西方/扬布里柯/哲学规劝录 哲学的慰藉.pdf'
TITLE = '哲学规劝录 哲学的慰藉'
AUTHOR = '扬布里柯、波爱修斯'
bid = hashlib.md5(REL.encode()).hexdigest()[:12]

# (标题, 起始物理页, 结束物理页) — 边界来自 ckpt 页级扫描（2026-08-09）
SECTIONS = [
    ("序言与目录", 1, 13),
    ("中译者前言", 14, 17),
    ("第一章 总论哲学规劝及其方式", 18, 18),
    ("第二章 通过谚语来进行规劝", 19, 20),
    ("第三章 毕达哥拉斯派的格言规劝", 21, 25),
    ("第四章 阿尔基塔的哲学规劝", 26, 30),
    ("第五章 毕达哥拉斯派的理论性规劝", 31, 39),
    ("第六章 哲学对现实生活有益", 40, 42),
    ("第七章 智慧本身就值得追求", 43, 45),
    ("第八章 智慧让人生有了价值", 46, 48),
    ("第九章 智慧是人的终极目的", 49, 52),
    ("第十章 理论性的哲学可以指导实践", 53, 53),
    ("第十一章 理性生活给人带来快乐", 54, 56),
    ("第十二章 哲学带来最大的幸福", 57, 57),
    ("第十三章 哲学使灵魂超脱肉体", 58, 65),
    ("第十四章 哲学使人藐视世俗价值", 66, 68),
    ("第十五章 哲学让人摆脱无教养的洞穴状态", 69, 71),
    ("第十六章 哲学让灵魂之眼转向善", 72, 73),
    ("第十七章 用比喻的方式劝人节制", 74, 74),
    ("第十八章 灵魂与身体一样需要健康", 75, 76),
    ("第十九章 灵魂的美德胜过其他各种好处", 77, 79),
    ("第二十章 社会生活的秩序需要哲学", 80, 86),
    ("第二十一章 毕达哥拉斯派的信条", 87, 104),
    ("附录一 毕达哥拉斯的《金诗》", 105, 109),
    ("附录二 扬布里柯的若干残篇", 110, 115),
    ("附录三 普罗克洛关于占星神谕的评注（摘录）", 116, 120),
    ("代译序 一代文宗波爱修及其《哲学的慰藉》", 121, 133),
    ("卷一 问疾篇", 134, 152),
    ("卷二 祛蔽篇", 153, 174),
    ("卷三 卸轭篇", 175, 210),
    ("卷四 慰心篇", 211, 239),
    ("卷五 解惑篇", 240, 258),
    ("译名对照表", 259, 264),
    ("后记", 265, 267),
]

# 标题行模式（整行匹配才参与 seen-set 去重）
TITLE_PATS = [
    re.compile(r'^第[一二三四五六七八九十]{1,3}章.{0,40}$'),
    re.compile(r'^附录[一二三].{0,40}$'),
    re.compile(r'^卷[一二三四五].{0,12}$'),
    re.compile(r'^[一二三四五六七八九十]{1,2}[^一二三四五六七八九十]{1,35}$'),
    re.compile(r'^后记$'),
    re.compile(r'^中译者前言$'),
    re.compile(r'^译名对照表$'),
    re.compile(r'^一代文宗.{0,20}$'),
    re.compile(r'^目录$'),
]
# 带书名前缀的页眉行（"哲学规劝录|第X章…" "哲学的慰藉|卷X…" "哲学规劝录·哲学的慰藉丨目 录"）
HEADER_RE = re.compile(r'^[^|丨]{0,20}(哲学规劝录|哲学的慰藉)[^|丨]{0,20}[|丨].{0,50}$')
FOOT_RE = re.compile(r'^\d{1,4}$')
def norm_key(s):
    return re.sub(r'[\s|丨·*]', '', s)

def clean_page(text):
    """清理单页: 删页眉/页脚/重复标题行, 返回 (保留行, 更新后的 seen)"""
    seen = set()
    out = []
    for line in text.split('\n'):
        ln = line.strip()
        if not ln:
            continue
        if FOOT_RE.match(ln):            # 页脚页码
            continue
        if HEADER_RE.match(ln):          # 带书名前缀页眉
            continue
        key = norm_key(ln)
        for p in TITLE_PATS:
            if p.match(ln) and len(key) <= 45:
                if key in seen:
                    ln = None            # 重复标题行（页眉）删除
                else:
                    seen.add(key)
                break
        if ln is not None:
            out.append(line)
    return out, seen

def main():
    ckpt = json.load(open(CKPT, encoding='utf-8'))
    safe = re.sub(r'[^\w\-.]', '_', REL)
    ocr = ckpt.get('ocr', {}).get(safe, {})
    pages = {int(k): v for k, v in ocr.items() if v and v != '__FAILED__'}

    sys.path.insert(0, os.path.join(BASE, 'tools'))
    import importlib.util
    spec = importlib.util.spec_from_file_location('dpp', os.path.join(BASE, 'tools', 'dp_pdf_import.py'))
    dpp = importlib.util.module_from_spec(spec)
    _save = sys.argv
    sys.argv = ['dp_pdf_import.py']
    try:
        spec.loader.exec_module(dpp)
    finally:
        sys.argv = _save

    D = os.path.join(BASE, 'data', 'book_chapters', bid)
    if os.path.isdir(D):
        shutil.rmtree(D)
    os.makedirs(D)
    toc = []
    for idx, (title, ps, pe) in enumerate(SECTIONS):
        lines = []
        seen = set()
        for p in range(ps, pe + 1):
            txt = pages.get(p, '')
            if not txt:
                continue
            kept, seen = clean_page(txt)
            lines.extend(kept)
        text = '\n'.join(lines)
        ch = {'index': idx, 'title': title, 'content': dpp.to_blocks(text)}
        json.dump(ch, open(os.path.join(D, f'{idx}.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        toc.append(title)
        print(f'  [{idx:2d}] {title[:34]:<36} {len(text):>7} 字符 (页 {ps}-{pe})', flush=True)
    meta = {'bookId': bid, 'title': TITLE, 'author': AUTHOR, 'toc': toc,
            'cover': None, 'chapterCount': len(toc), 'chapterTitles': toc}
    json.dump(meta, open(os.path.join(D, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('已重建:', bid, '|', len(toc), '章', flush=True)

    # public 双写（覆盖, 旧 43 章副本必须被替换）
    os.makedirs(PUBLIC, exist_ok=True)
    dst = os.path.join(PUBLIC, bid)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(D, dst)
    print('public 双写完成:', dst, flush=True)

    # detail 同步（保留 rank/tags/summary/cover, 更新 chapterCount/toc/chapterTitles）
    dp = os.path.join(DETAIL_DIR, f'{bid}.json')
    det = json.load(open(dp, encoding='utf-8')) if os.path.exists(dp) else {}
    det.update({'bookId': bid, 'title': TITLE, 'author': AUTHOR, 'chapterCount': len(toc),
                'toc': toc, 'chapterTitles': toc})
    json.dump(det, open(dp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('detail 更新:', dp, '| chapterCount =', det.get('chapterCount'), flush=True)

if __name__ == '__main__':
    main()
