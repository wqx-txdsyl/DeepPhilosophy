# -*- coding: utf-8 -*-
"""黑格尔作品集源 epub：ncx/toc 结构 + 册边界"""
import zipfile, re, os

EPUB = 'f:/philosophy/西方/格奥尔格·威廉·弗里德里希·黑格尔/黑格尔作品集（套装共14册）.epub'
z = zipfile.ZipFile(EPUB)
names = z.namelist()
print('文件数:', len(names))
htmls = [n for n in names if n.endswith(('.html', '.xhtml', '.htm'))]
print('html:', len(htmls))
print('前15:', htmls[:15])
print('后15:', htmls[-15:])
# ncx 读取
ncx = [n for n in names if 'ncx' in n.lower() or 'toc' in n.lower()]
print('ncx/toc 文件:', ncx)
for n in ncx[:1]:
    t = z.read(n).decode('utf-8', errors='ignore')
    # 提取 navPoint 标题
    titles = re.findall(r'<text>(.*?)</text>', t, re.S)
    print('=== %s navPoint 标题数: %d ===' % (n, len(titles)))
    for x in titles[:80]:
        print('   ', re.sub(r'\s+', ' ', x)[:60])
