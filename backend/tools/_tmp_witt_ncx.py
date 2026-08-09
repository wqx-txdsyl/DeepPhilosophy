# -*- coding: utf-8 -*-
"""完整解析 toc.ncx 层级树: navPoint 深度 → 标题 + src 指向的 part + 该 part 实际字符量"""
import zipfile, re

EP = r'F:/philosophy/西方/路德维希·维特根斯坦/《维特根斯坦文集（套装全8卷）》.epub'

with zipfile.ZipFile(EP) as z:
    ncx = z.read('toc.ncx').decode('utf-8', 'ignore')
    # 提取 navPoint 序列 (含嵌套), 记录深度
    pat = re.compile(r'<navPoint[^>]*>.*?<navLabel>\s*<text>(.*?)</text>.*?<content[^>]*src="([^"]*)"[^>]*/?>', re.S)
    # 用计数器法: 每遇到 <navPoint 深度+1, </navPoint> 深度-1
    parts = []
    depth = 0
    pos = 0
    while True:
        op = ncx.find('<navPoint', pos)
        cl = ncx.find('</navPoint>', pos)
        if op == -1 or cl == -1:
            break
        if op < cl:
            # 开标签: 读 text 和 src
            seg = ncx[op:ncx.find('>', op) + 1]
            depth += 1
            seg2 = ncx[op:ncx.find('</navPoint>', op)]
            t = re.search(r'<text>(.*?)</text>', seg2, re.S)
            s = re.search(r'<content[^>]*src="([^"]*)"', seg2)
            parts.append((depth, t.group(1).strip() if t else '?', s.group(1) if s else ''))
            pos = op + 1
        else:
            depth -= 1
            pos = cl + 1
    print('navPoint 总数:', len(parts))

    # 每 part 文件字符量
    def size(p):
        try:
            return len(z.read(p).decode('utf-8', 'ignore'))
        except Exception:
            return -1

    for depth, t, src in parts:
        # 展开 src 到实际 part
        srcs = src if src else '(无src)'
        chars = ''
        if src:
            # 可能带 #anchor
            fn = src.split('#')[0]
            chars = str(size(fn))
        print('  ' * (depth - 1) + '[%d] %s | src=%s | 字符=%s' % (depth, t[:50], srcs, chars))
