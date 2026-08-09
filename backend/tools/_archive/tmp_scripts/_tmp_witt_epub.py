# -*- coding: utf-8 -*-
"""探查维特根斯坦文集 epub 的导航结构（nav/opf/spine + 每 part 标题）"""
import zipfile, re, os

EP = r'F:/philosophy/西方/路德维希·维特根斯坦/《维特根斯坦文集（套装全8卷）》.epub'

with zipfile.ZipFile(EP) as z:
    names = z.namelist()
    # 找 nav / toc 文件
    navs = [n for n in names if 'nav' in n.lower() or 'toc' in n.lower() or n.endswith('.ncx')]
    print('nav/toc 文件:', navs)
    # opf 内容
    opf = z.read('content.opf').decode('utf-8', errors='ignore')
    m = re.search(r'<spine[^>]*>(.*?)</spine>', opf, re.S)
    if m:
        items = re.findall(r'<itemref[^>]+idref="([^"]+)"', m.group(1))
        print('spine itemref 数:', len(items))

    # 读 nav（若存在）
    navf = [n for n in navs if n.endswith(('.xhtml', '.html'))]
    if navf:
        nav = z.read(navf[0]).decode('utf-8', errors='ignore')
        # 提取 toc 树
        tags = re.findall(r'<a[^>]*>(.*?)</a>', nav, re.S)
        texts = [re.sub(r'<[^>]+>', '', t).strip() for t in tags]
        texts = [t for t in texts if t]
        print('nav 目录项数:', len(texts))
        for t in texts[:50]:
            print('  ', t[:60])
    else:
        print('无 nav 文件, 看 ncx:')
        ncx = [n for n in navs if n.endswith('.ncx')]
        if ncx:
            c = z.read(ncx[0]).decode('utf-8', errors='ignore')
            texts = re.findall(r'<text>(.*?)</text>', c, re.S)
            print('ncx 目录项数:', len(texts))
            for t in texts[:50]:
                print('  ', t[:60])

    # 抽查各 part 标题（前 12 个 + 中间几个）
    print()
    print('=== part 文件标题 ===')
    parts = sorted([n for n in names if re.match(r'text/part\d+', n) and n.endswith('.html')],
                   key=lambda n: (int(re.search(r'part(\d+)', n).group(1)), n))
    for p in parts[:14] + parts[-6:]:
        html = z.read(p).decode('utf-8', errors='ignore')
        h = re.search(r'<h[1-4][^>]*>(.*?)</h[1-4]>', html, re.S)
        t = re.search(r'<title>(.*?)</title>', html, re.S)
        htext = re.sub(r'<[^>]+>', '', h.group(1)).strip()[:50] if h else ''
        ttext = t.group(1).strip()[:50] if t else ''
        print('  %s | h: %s | title: %s' % (p, htext, ttext))
