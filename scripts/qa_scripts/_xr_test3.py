# -*- coding: utf-8 -*-
import json, re, importlib.util
spec = importlib.util.spec_from_file_location('m', '_xr_rebuild_aquinas6.py')
m = importlib.util.module_from_spec(spec)
# 不执行主流程：手动构造
CK = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
SAFE = '西方_托马斯_阿奎那_神学大全_第一集_第6卷.pdf'
ck = json.load(open(CK, encoding='utf-8'))
p33 = ck['ocr'][SAFE]['33']
EVEN_HDR = re.compile(r'^\d{1,4}第.卷论人\s*$')
ODD_HDR = re.compile(r'^问题\d+[^\d][^\n]{0,49}\d{1,4}\s*$')
MARG = re.compile(r'^\d{3,4}[a-z]?\s*$')
INLINE_MARGIN = re.compile(r'(?<=[一-鿿])\d{3,4}[a-z]$')
def clean_page(txt):
    lines = []
    for ln in txt.split('\n'):
        s = ln.strip()
        if not s:
            continue
        if EVEN_HDR.match(s) or ODD_HDR.match(s) or MARG.match(s):
            continue
        s = INLINE_MARGIN.sub('', s)
        if s:
            lines.append(s)
    return '\n'.join(lines)
out = clean_page(p33)
print('clean_page 后 447b 是否在:', '447b' in out)
for ln in out.split('\n'):
    if '447b' in ln:
        print('残留行 repr:', repr(ln))
