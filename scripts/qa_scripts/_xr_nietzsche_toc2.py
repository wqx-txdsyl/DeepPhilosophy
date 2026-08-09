# -*- coding: utf-8 -*-
"""找尼采 epub 里 Contents 目录页并打印"""
import zipfile, re, html as h

for path in ['F:/philosophy/西方/弗里德里希·尼采/尼采经典著作及研究丛书（四册全）.epub',
             'F:/philosophy/new/100本哲学书单全收录/25尼采经典著作及研究丛书（四册全）/尼采经典著作及研究丛书（四册全） - 尼采 & 孙周兴.epub']:
    print('===', path)
    try:
        z = zipfile.ZipFile(path)
    except Exception as e:
        print('  打不开:', e)
        continue
    names = z.namelist()
    print('  文件数:', len(names))
    # 找含 Contents/目录 的 html
    for n in names:
        if not n.endswith(('.html', '.xhtml', '.htm')):
            continue
        t = z.read(n).decode('utf-8', errors='ignore')
        if '第一编' in t and '虚无' in t and '目录' in t:
            body = re.sub(r'<[^>]+>', '|', t)
            body = h.unescape(body)
            lines = [l.strip() for l in body.split('|') if l.strip()]
            print('  Contents 页:', n, '行数:', len(lines))
            for l in lines[:100]:
                print('   ', l)
            break
    print()
