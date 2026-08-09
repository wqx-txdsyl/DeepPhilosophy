# -*- coding: utf-8 -*-
"""读 epub 元数据找《反杜林论》导读作者 + 检查 9 本书在所有数据源的 author 现状"""
import json, os, zipfile, re

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
PHI = r'F:/program/Python/PhiAgent/backend/data'

epub = r'F:/philosophy/西方/弗里德里希·恩格斯/《反杜林论》导读.epub'
z = zipfile.ZipFile(epub)
opf_name = [n for n in z.namelist() if n.endswith('.opf')][0]
opf = z.read(opf_name).decode('utf-8', errors='replace')
print('== epub 作者 ==')
for m in re.finditer(r'<dc:creator[^>]*>(.*?)</dc:creator>', opf):
    print('  creator:', m.group(1))
print('  title:', re.search(r'<dc:title[^>]*>(.*?)</dc:title>', opf).group(1))

# 9 本书 (8 系列 + 1 导读, 反杜林导读算进来)
BIDS = {
    '帕斯卡尔': 'd036e1e712eb',
    '莱布尼茨': '75efcbb151b7',
    '克尔恺廓尔': 'add6c213fde8',
    '苏格拉底': 'cba9d40254dc',
    '尼采': '00fadd7de47c',
    '梅洛-庞蒂': '324c13db486e',
    '导读福柯': '60eed962806b',
    '导读德勒兹': '7f462a9750e8',
    '反杜林论导读': '62c5caa0bfde',
}
print()
print('== 各数据源 author 现状 ==')
for name, bid in BIDS.items():
    row = [name]
    # books.json
    bj = json.load(open(BASE + '/app/public/books.json', encoding='utf-8'))
    items = bj if isinstance(bj, list) else bj.get('books', [])
    hit = next((it for it in items if it.get('id') == bid), None)
    row.append('books.json=' + (hit.get('author', '?') if hit else '?无条目?'))
    # DP 两处 detail
    for p in [BASE + '/backend/data/book_detail', BASE + '/app/public/book_detail']:
        fp = p + '/' + bid + '.json'
        row.append('detail=' + (json.load(open(fp, encoding='utf-8')).get('author', '?') if os.path.exists(fp) else '缺失'))
    # DP 两处 meta
    for p in [BASE + '/backend/data/book_chapters', BASE + '/app/public/backend/data/book_chapters']:
        fp = p + '/' + bid + '/meta.json'
        row.append('meta=' + (json.load(open(fp, encoding='utf-8')).get('author', '?') if os.path.exists(fp) else '缺失'))
    # PhiAgent 副本
    fpd = PHI + '/book_detail/' + bid + '.json'
    fpm = PHI + '/book_chapters/' + bid + '/meta.json'
    row.append('PHI_detail=' + (json.load(open(fpd, encoding='utf-8')).get('author', '?') if os.path.exists(fpd) else '无'))
    row.append('PHI_meta=' + (json.load(open(fpm, encoding='utf-8')).get('author', '?') if os.path.exists(fpm) else '无'))
    print('  '.join(row))
