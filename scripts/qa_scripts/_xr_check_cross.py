# -*- coding: utf-8 -*-
"""OCR 完成书 vs CHKLIST 逐本状态交叉比对"""
import json, re, hashlib

ck = json.load(open('f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
cklist = open('f:/program/Python/PhiAgent/backend/tools/CHKLIST.md', encoding='utf-8').read()
rows = re.findall(r'\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([0-9a-f]{12})\s*\|', cklist)
st_by_bid = {r[2]: (int(r[0]), r[1].strip()) for r in rows}

books = ck['books']
def safe_of(rel):
    return re.sub(r'[^A-Za-z0-9一-鿿.]', '_', rel)
rel_by_safe = {safe_of(rel): rel for rel in books}

ocr = ck['ocr']
checked, unchecked = [], []
for safe in ocr:
    rel = rel_by_safe.get(safe, safe)
    bid = hashlib.md5(rel.encode()).hexdigest()[:12]
    st = st_by_bid.get(bid)
    m = re.search(r'\|\s*\d+\s*\|\s*[^|]*?\s*\|\s*' + bid + r'\s*\|\s*[^|]*?\s*\|\s*([^|]+?)\s*\|', cklist)
    status = m.group(1).strip() if m else '(CHKLIST无此bid)'
    name = st[1] if st else safe[:40]
    (checked if status.startswith(('✅', '✓')) else unchecked).append(
        (st[0] if st else 9999, name, status))

print('OCR完成57本: 已核验 %d | 未核验/待定 %d' % (len(checked), len(unchecked)))
print()
for c in sorted(checked):
    print('  已: #%-3s %s [%s]' % (c[0], c[1][:38], c[2]))
print()
for c in sorted(unchecked, key=lambda x: x[0]):
    print('  待: #%-3s %s [%s]' % (c[0], c[1][:38], c[2]))
