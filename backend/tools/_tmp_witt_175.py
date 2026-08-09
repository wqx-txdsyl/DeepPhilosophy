# -*- coding: utf-8 -*-
import zipfile, re
EP = r'F:/philosophy/西方/路德维希·维特根斯坦/《维特根斯坦文集（套装全8卷）》.epub'
with zipfile.ZipFile(EP) as z:
    ncx = z.read('toc.ncx').decode('utf-8', 'ignore')
    for m in re.finditer(r'<navPoint[^>]*>.*?</navPoint>', ncx, re.S):
        seg = m.group(0)
        if 'MS 175' in seg or 'MS 177' in seg:
            t = re.search(r'<text>(.*?)</text>', seg, re.S)
            s = re.search(r'<content[^>]*src="([^"]*)"', seg)
            print(repr(t.group(1)) if t else '?', '|', s.group(1) if s else '?')
